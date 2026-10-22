"""Repeatable A-H release checks against a disposable, stopped backend.

All counts originate in SUMO or real inference. Optional artificial history is
explicitly opted into and labeled; it is never represented as measured history.
"""
import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import time
import httpx
from websockets.sync.client import connect


def demonstrate(base, output, selected='all', example_forecast=False):
    results = []
    output = Path(output)
    def save(complete=False):
        output.write_text(json.dumps(dict(createdUtc=datetime.now(timezone.utc).isoformat(), complete=complete,
                                         results=results, learnedPolicyActivated=False,
                                         limitations='Research demonstration; scripted SUMO demand, not field validation or comparative performance'), indent=2), encoding='utf-8')
    with httpx.Client(base_url=base.rstrip('/')+'/', timeout=30) as client:
        def get(path):
            response = client.get(path); response.raise_for_status(); return response.json()
        def post(path, **kwargs):
            response = client.post(path, **kwargs); response.raise_for_status(); return response.json()
        if get('sumo/status')['connected'] or get('perception/status')['available']:
            raise RuntimeError('Use a stopped disposable backend; active SUMO/camera sessions are preserved')
        cases = [('A', 'normal_adaptive', 'vehicle', 140), ('B', 'unequal_demand', 'unequal', 140),
                 ('C', 'blocked_exit_spillback', 'spillback', 80), ('D', 'pedestrian_protection', 'pedestrian', 180),
                 ('E', 'emergency_priority', 'pedestrian', 180), ('F', 'multi_junction', 'corridor', 180),
                 ('G', 'sensor_controller_fallback', 'corridor', 80), ('H', 'recorded_camera', None, 0)]
        for letter, name, scenario, steps in cases:
            if selected != 'all' and selected != letter:
                continue
            result = dict(id=letter, case=name, status='running', source='actual_http_websocket_sumo', seed=95)
            results.append(result)
            save()
            try:
                if letter == 'H':
                    response = client.post('perception/start')
                    if response.status_code == 409:
                        result.update(status='skipped', reason=response.json()['detail'])
                        print('H skipped: '+str(result['reason']), flush=True)
                        continue
                    response.raise_for_status()
                    deadline = time.monotonic()+25
                    observed = None
                    while time.monotonic() < deadline:
                        data = get('traffic-state?source=camera')
                        if data['source'] == 'camera_fusion' and data['traffic']['tracks']:
                            observed = data
                            frames = [c['lastFrame'] for c in data['perception']['cameras'].values() if c['lastFrame']]
                            if any(f['timestamp'] >= 1 for f in frames):
                                break
                        if any(c['state'] == 'failed' for c in data['perception']['cameras'].values()):
                            raise RuntimeError(str(data['perception']['cameras']))
                        time.sleep(.1)
                    assert observed is not None, 'No real tracked vehicle observations'
                    assert not observed['perception']['actuationEnabled']
                    result.update(status='passed', source='real_yolo_bytetrack_video',
                                  fusedCounts=observed['traffic']['approaches'],
                                  visibleTrackIds=[(r['cameraId'], r['trackId']) for r in observed['traffic']['tracks']],
                                  fieldAccuracyVerified=False)
                    post('perception/stop')
                    assert not get('perception/status')['available']
                    print('H passed: real recorded-video detections and stop fallback', flush=True)
                    continue
                if letter == 'A' and example_forecast:
                    # This is an explicit demo-only opt-in; the normal API blocks
                    # artificial history from MPC unless the operator enables it.
                    now = datetime.now(timezone.utc)
                    csv = 'timestamp,approach,arrivals_pcu,interval_sec\n'+'\n'.join(
                        f'{(now-timedelta(days=7)).isoformat()},{d},6,60' for d in ('north', 'south', 'east', 'west'))
                    post('forecast/history', json={'csv': csv, 'example_data': True})
                    post('forecast/config', json={'enabled': True, 'allow_example_for_mpc': True, 'weather_provider': 'manual'})
                    post('forecast/weather', json={'timestamp': now.isoformat(), 'rainfall_mm_h': 8, 'source': 'EXAMPLE DEMO FIXTURE; not measured weather'})
                    result['forecastProvenance'] = 'EXAMPLE ONLY; explicit demo opt-in, not operational historical validation'
                start = post('sumo/start', params=dict(scenario=scenario, controller='hybrid', seed=95, paused='true',
                                                      **({'mpc_budget_ms': 0} if letter == 'G' else {})))
                assert start['telemetry']['simTime'] == 0
                assert not start['mappoStatus']['operationalPolicyEnabled'], 'Demo must not activate a learned policy'
                if letter == 'G':
                    fallback = get('traffic-state?source=camera')
                    assert fallback['source'] == 'sumo_traci' and fallback['fallback']
                    result['missingCameraFallbackVerified'] = True
                emergency = post('sumo/emergencies/inject', json={'approach': 'east', 'priority': 3}) if letter == 'E' else None
                policies, forecast_used = set(), False
                max_occupancy, zero_supply, pedestrian_seen, clearance = 0.0, False, False, set()
                for _ in range(steps):
                    raw = post('sumo/step')
                    state = get('sumo/status')
                    assert state['error'] is None
                    assert all(row['compatibleUnderSumoRules'] for row in raw['permissionAnalysis'].values())
                    diagnostics = list(state['controllerDiagnostics'].values()) if scenario == 'corridor' else [state['controllerDiagnostics']]
                    for diag in diagnostics:
                        if diag:
                            policies.add(diag.get('policy'))
                            forecast_used |= diag.get('arrivalForecastSource') == 'seasonal_shrinkage_baseline'
                            zero_supply |= diag.get('receivingSupply', {}).get('north') == 0
                    max_occupancy = max(max_occupancy, raw['downstream']['south']['occupancyPercent'])
                    pedestrian_seen |= bool(raw['pedestrians'])
                    clearance.update(p['clearanceRequirementSec'] for p in raw['pedestrianSignals'] if p['clearanceRequirementSec'] is not None)
                with connect(base.replace('http', 'ws', 1).rstrip('/')+'/sumo/ws', open_timeout=10) as socket:
                    message = json.loads(socket.recv())
                    assert message['telemetry']['simTime'] == raw['simTime']
                    assert message['metrics'] == state['metrics']
                if letter == 'A' and example_forecast:
                    assert forecast_used and state['forecasts']['exampleData'] and state['forecasts']['weatherAvailable']
                if letter == 'B':
                    assert raw['stateEstimates']['north']['arrivalRatePerSec'] > raw['stateEstimates']['east']['arrivalRatePerSec']
                if letter == 'C':
                    assert max_occupancy >= 80 and zero_supply and raw['approaches']['north']['queued'] > 0
                if letter in {'D', 'E'}:
                    assert pedestrian_seen and 15 in clearance
                if letter == 'E':
                    request = next(r for r in state['emergencyPriority']['requests'] if r['vehicleId'] == emergency['vehicleId'])
                    assert request['state'] == 'completed' and 'emergency_priority' in policies
                    result['emergency'] = request
                if letter == 'F':
                    assert set(state['junctions']) == {'A0', 'B0'}
                    assert all(j['safetySupervisor']['acceptedActions'] > 0 for j in state['junctions'].values())
                if letter == 'G':
                    assert 'max_pressure_fallback' in policies
                else:
                    assert 'constrained_mpc' in policies
                result.update(status='passed', simTime=raw['simTime'], policies=sorted(str(p) for p in policies),
                              metrics=state['metrics'], websocketMatched=True, forecastUsed=forecast_used,
                              maxSouthOccupancyPercent=max_occupancy, zeroNorthReceivingSupplyObserved=zero_supply,
                              pedestrianSeen=pedestrian_seen, pedestrianClearanceSec=sorted(clearance),
                              approachQueues={d:r['queued'] for d,r in raw['approaches'].items()})
                print(letter+' passed: '+name+' ('+str(raw['simTime'])+' simulated seconds)', flush=True)
            except Exception as exc:
                result.update(status='failed', error=str(exc))
                raise
            finally:
                if scenario:
                    post('sumo/stop')
                else:
                    post('perception/stop')
                if letter == 'A' and example_forecast:
                    post('forecast/config', json={'enabled': False})
                save()
        save(complete=True)
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:8022/api/v1')
    parser.add_argument('--output', default='.checkpoints/stage3-demo-results.json')
    parser.add_argument('--scenario', choices=['all', *'ABCDEFGH'], default='all')
    parser.add_argument('--with-example-forecast', action='store_true')
    args = parser.parse_args()
    demonstrate(args.base_url, args.output, args.scenario, args.with_example_forecast)
