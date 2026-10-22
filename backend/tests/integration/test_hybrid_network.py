"""Actual SUMO/API/WebSocket corridor tests. No fake traffic or signal writes."""
import json
from pathlib import Path
import shutil
import pytest
import traci
from fastapi.testclient import TestClient
from app.main import app
from app.services.sumo_runtime import sumo_runtime

pytestmark = pytest.mark.skipif(shutil.which('sumo') is None, reason='SUMO required')


def test_corridor_hybrid_api_websocket_emergency_and_timeout(tmp_path, monkeypatch):
    monkeypatch.delenv('SYNCHROFLOW_MAPPO_CHECKPOINT', raising=False)
    monkeypatch.delenv('SYNCHROFLOW_MAPPO_VALIDATION', raising=False)
    with TestClient(app) as client:
        try:
            start = client.post('/api/v1/sumo/start?scenario=corridor&controller=hybrid&seed=73&paused=true')
            assert start.status_code == 200, start.text
            assert start.json()['telemetry']['simTime'] == 0
            assert set(start.json()['junctions']) == {'A0', 'B0'}
            assert not start.json()['mappoStatus']['operationalPolicyEnabled']
            assert client.post('/api/v1/sumo/start?seed=74').status_code == 409
            injection = client.post('/api/v1/sumo/emergencies/inject', json={'approach': 'north', 'priority': 3, 'junctionId': 'B0'})
            assert injection.status_code == 200, injection.text
            emergency_id = injection.json()['vehicleId']
            seen_policies = {a: set() for a in ('A0', 'B0')}
            stages = {a: set() for a in ('A0', 'B0')}
            original_write = traci.trafficlight.setPhaseDuration
            applied = []
            def audited_write(agent, duration):
                supervisor = sumo_runtime.network.controllers[agent].supervisor
                phase = traci.trafficlight.getPhase(agent)
                # Audit at the actual TraCI write boundary.
                supervisor.validate_duration(phase, traci.trafficlight.getSpentDuration(agent), duration, traci.simulation.getTime())
                applied.append((agent, phase, duration))
                return original_write(agent, duration)
            monkeypatch.setattr(traci.trafficlight, 'setPhaseDuration', audited_write)
            for _ in range(180):
                response = client.post('/api/v1/sumo/step')
                assert response.status_code == 200, response.text
                state = client.get('/api/v1/sumo/status').json()
                for agent, junction in state['junctions'].items():
                    stages[agent].add(junction['telemetry']['trafficLights'][agent]['phaseIndex'])
                    diagnostics = junction['controllerDiagnostics']
                    seen_policies[agent].add(diagnostics.get('policy'))
                    assert junction['telemetry']['permissionAnalysis'][agent]['compatibleUnderSumoRules']
            assert applied and {a for a, _, _ in applied} == {'A0', 'B0'}
            assert all('constrained_mpc' in policies for policies in seen_policies.values())
            assert all(stages[a] == set(range(6)) for a in stages)
            requests = state['junctions']['B0']['emergencyPriority']['requests']
            assert next(r for r in requests if r['vehicleId'] == emergency_id)['state'] == 'completed'
            assert 'emergency_priority' in seen_policies['B0']
            assert state['metrics']['arrivedVehicles'] > 0 and state['metrics']['queueVehicleSeconds'] >= 0
            with client.websocket_connect('/api/v1/sumo/ws') as socket:
                message = socket.receive_json()
                assert message['junctions'] == state['junctions']
                assert message['metrics'] == state['metrics']
            sumo_runtime.network.controllers['A0'].SOLVE_BUDGET_SEC = 0
            fallback = False
            for _ in range(60):
                assert client.post('/api/v1/sumo/step').status_code == 200
                diagnostics = sumo_runtime.network.controllers['A0'].diagnostics
                if diagnostics.get('policy') == 'max_pressure_fallback':
                    assert 'budget' in diagnostics['fallback']
                    fallback = True
                    break
            assert fallback
            report = dict(source='actual_sumo_api_websocket', scenario='corridor', seed=73,
                          metrics=state['metrics'], policies={a: sorted(str(p) for p in ps) for a, ps in seen_policies.items()},
                          auditedTimingWrites=len(applied), emergencyCompleted=True, timeoutFallback=True, mappoEnabled=False)
            Path(tmp_path/'corridor-report.json').write_text(json.dumps(report, indent=2))
        finally:
            client.post('/api/v1/sumo/stop')
            sumo_runtime.scenario, sumo_runtime.controller_mode = 'vehicle', 'sumo_fixed_time'


def test_bad_policy_fallback_and_supervisor_fault_pause(monkeypatch):
    monkeypatch.setenv('SYNCHROFLOW_MAPPO_CHECKPOINT', 'missing-policy.pt')
    monkeypatch.setenv('SYNCHROFLOW_MAPPO_VALIDATION', 'missing-validation.json')
    with TestClient(app) as client:
        try:
            start = client.post('/api/v1/sumo/start?scenario=corridor&controller=hybrid&paused=true')
            assert start.status_code == 200, start.text
            assert start.json()['seed'] == 23423  # prior session seed must not leak
            assert not start.json()['mappoStatus']['operationalPolicyEnabled']
            assert 'fallback' in start.json()['mappoStatus']['reason']
            for _ in range(12):
                assert client.post('/api/v1/sumo/step').status_code == 200
            c = sumo_runtime.network.controllers['A0']
            before = traci.trafficlight.getPhase('A0')
            time_before = traci.simulation.getTime()
            traci.trafficlight.setPhase('A0', (before+2) % 6)  # deliberate feedback corruption
            assert client.post('/api/v1/sumo/step').status_code == 409
            status = client.get('/api/v1/sumo/status').json()
            assert not status['running'] and 'Live signal feedback differs' in status['error']
            assert traci.simulation.getTime() == time_before
        finally:
            client.post('/api/v1/sumo/stop')
            sumo_runtime.scenario, sumo_runtime.controller_mode = 'vehicle', 'sumo_fixed_time'
