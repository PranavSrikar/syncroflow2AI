"""Run five actual HTTP/WebSocket/SUMO scenarios against a disposable backend."""
import argparse
import json
from pathlib import Path
import httpx
from websockets.sync.client import connect


def verify(base, output):
    results = []
    with httpx.Client(base_url=base.rstrip('/')+'/', timeout=30) as client:
        def post(path, **kwargs):
            response = client.post(path, **kwargs)
            response.raise_for_status()
            return response.json()
        if client.get('sumo/status').json()['connected']:
            raise RuntimeError('Use a disposable stopped backend; refusing to replace an active simulation')
        cases = [('single_adaptive', 'vehicle', 140, False, None),
                 ('pedestrian_protection', 'pedestrian', 180, False, None),
                 ('emergency_priority', 'pedestrian', 180, True, None),
                 ('multi_junction', 'corridor', 180, True, None),
                 ('solver_timeout_fallback', 'corridor', 80, False, 0)]
        for name, scenario, steps, emergency, budget in cases:
            policies, pedestrian_seen, clearances, emergency_id = set(), False, set(), None
            try:
                params = dict(scenario=scenario, controller='hybrid', seed=95, paused='true')
                if budget is not None:
                    params['mpc_budget_ms'] = budget
                start = post('sumo/start', params=params)
                assert start['telemetry']['simTime'] == 0
                if emergency:
                    payload = dict(approach='east' if scenario == 'pedestrian' else 'north', priority=3)
                    if scenario == 'corridor':
                        payload['junctionId'] = 'B0'
                    emergency_id = post('sumo/emergencies/inject', json=payload)['vehicleId']
                for _ in range(steps):
                    raw = post('sumo/step')
                    pedestrian_seen = pedestrian_seen or bool(raw['pedestrians'])
                    clearances.update(p['clearanceRequirementSec'] for p in raw['pedestrianSignals'] if p['clearanceRequirementSec'] is not None)
                    status = client.get('sumo/status').json()
                    diagnostics = status['controllerDiagnostics']
                    if scenario == 'corridor':
                        policies.update(d.get('policy') for d in diagnostics.values() if d)
                    elif diagnostics:
                        policies.add(diagnostics.get('policy'))
                    assert all(a['compatibleUnderSumoRules'] for a in raw['permissionAnalysis'].values())
                with connect(base.replace('http', 'ws', 1).rstrip('/')+'/sumo/ws', open_timeout=10) as socket:
                    stream = json.loads(socket.recv())
                    assert stream['telemetry']['simTime'] == raw['simTime']
                    assert stream['metrics'] == status['metrics']
                request = next((r for r in status['emergencyPriority']['requests'] if r['vehicleId'] == emergency_id), None)
                if emergency:
                    assert request and request['state'] == 'completed', request
                    assert 'emergency_priority' in policies
                if scenario == 'pedestrian':
                    assert pedestrian_seen and 15 in clearances
                if budget == 0:
                    assert 'max_pressure_fallback' in policies
                else:
                    assert 'constrained_mpc' in policies
                if scenario == 'corridor':
                    assert set(status['junctions']) == {'A0', 'B0'}
                results.append(dict(case=name, source='actual_http_websocket_sumo', seed=95, simTime=raw['simTime'],
                                    policies=sorted(str(p) for p in policies), metrics=status['metrics'],
                                    pedestrianSeen=pedestrian_seen, pedestrianClearances=sorted(clearances),
                                    emergency=request, mappoPolicyEnabled=status['mappoStatus']['operationalPolicyEnabled'],
                                    websocketMatched=True, error=status['error']))
                Path(output).write_text(json.dumps(dict(results=results, complete=False), indent=2), encoding='utf-8')
            finally:
                post('sumo/stop')
    report = dict(results=results, limitations='Execution and invariant verification only; no trained-policy or optimization-quality claim')
    Path(output).write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:8022/api/v1')
    parser.add_argument('--output', default='.checkpoints/stage2-end-to-end.json')
    args = parser.parse_args()
    report = verify(args.base_url, args.output)
    print(json.dumps([{'case': r['case'], 'simTime': r['simTime'], 'passed': r['error'] is None} for r in report['results']], indent=2))
