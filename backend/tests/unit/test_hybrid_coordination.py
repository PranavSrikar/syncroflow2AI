from pathlib import Path
import json
import numpy as np
import pytest
from app.services.mappo_coordination import MAPPOCoordinator
from app.services.forecasting import ForecastService, ForecastSettings
from app.services.signal_supervisor import SignalSupervisor
from app.services.sumo_network_safety import NetworkSafetyModel
from app.services.max_pressure_controller import MaxPressureController


def test_missing_bad_and_unqualified_policy_falls_back(monkeypatch, tmp_path):
    monkeypatch.delenv('SYNCHROFLOW_MAPPO_CHECKPOINT', raising=False)
    monkeypatch.delenv('SYNCHROFLOW_MAPPO_VALIDATION', raising=False)
    manager = MAPPOCoordinator(('A0', 'B0'))
    assert manager.recommend(np.zeros((2, 8))) is None
    assert not manager.snapshot()['operationalPolicyEnabled']
    validation = tmp_path/'validation.json'
    validation.write_text(json.dumps({'eligibleForEvaluation': True, 'trainedDecisionSteps': 48}))
    manager = MAPPOCoordinator(('A0', 'B0'), str(tmp_path/'missing.pt'), str(validation))
    assert manager.model is None
    assert manager.snapshot()['reason'].endswith('supervised MPC fallback')


def test_safety_only_evidence_cannot_enable_policy(monkeypatch, tmp_path):
    import hashlib
    from app.services.mappo_coordination import qualification_fingerprint
    weights = tmp_path/'candidate.pt'
    weights.write_bytes(b'not-a-qualified-policy')
    report = dict(checkpointSha256=hashlib.sha256(weights.read_bytes()).hexdigest(),
                  architectureFingerprint=qualification_fingerprint(), eligibleForEvaluation=True,
                  trainedDecisionSteps=1024, numericalChecksPassed=True,
                  closedLoopValidation=dict(seeds=[901,902,903],secondsPerSeed=300,safetyFaults=0))
    validation = tmp_path/'qualification.json'
    validation.write_text(json.dumps(report))
    coordinator = MAPPOCoordinator(('A0','B0'),weights,validation)
    assert coordinator.model is None
    assert not coordinator.snapshot()['operationalPolicyEnabled']


def test_inference_preferences_and_failure_are_bounded(monkeypatch):
    monkeypatch.delenv('SYNCHROFLOW_MAPPO_CHECKPOINT', raising=False)
    monkeypatch.delenv('SYNCHROFLOW_MAPPO_VALIDATION', raising=False)
    manager = MAPPOCoordinator(('A0', 'B0'))
    class FixturePolicy:
        def act(self, obs, deterministic):
            return np.array([0, 1]), None, None
    manager.model = FixturePolicy()  # explicit interface fixture, no trained-policy claim
    np.testing.assert_array_equal(manager.recommend(np.zeros((2, 8))), [0, 1])
    assert manager.inference_calls == 1
    assert manager.recommend(np.full((2, 8), np.nan)) is None
    with pytest.raises(ValueError):
        manager.validate_actions([2, 0])
    with pytest.raises(ValueError):
        manager.validate_actions([0])


def test_clearance_only_observes_its_own_junction():
    path = Path(__file__).resolve().parents[2]/'sumo_scenarios/two_junction/corridor.net.xml'
    supervisor = SignalSupervisor(NetworkSafetyModel(path), 'A0')
    assert not supervisor.clearance_occupied({'vehicleDetails': {'v': {'roadId': ':B0_4'}}})
    assert supervisor.clearance_occupied({'vehicleDetails': {'v': {'roadId': ':A0_4'}}})


def test_forecast_history_is_scoped_to_junction():
    from datetime import datetime, timezone
    service = ForecastService()
    service.configure(ForecastSettings(enabled=True))
    service.ingest_csv('timestamp,junction_id,approach,arrivals_pcu,interval_sec\n'
                       '2026-10-21T08:00:00Z,A0,north,12,60\n2026-10-21T08:00:00Z,B0,north,3,60')
    at = datetime(2026, 10, 22, 8, tzinfo=timezone.utc)
    a = service.predict(at, junction_id='A0')['approaches']['north']['steps'][0]
    b = service.predict(at, junction_id='B0')['approaches']['north']['steps'][0]
    assert a['arrivalRatePcuPerSec'] == pytest.approx(.2)
    assert b['arrivalRatePcuPerSec'] == pytest.approx(.05)
    assert not service.predict(at)['available']


def test_receiver_supply_follows_next_route_edge_and_spillback():
    controller = object.__new__(MaxPressureController)
    raw = {'approaches': {'north': {'vehicleIds': ['v']}},
           'vehicleDetails': {'v': {'routeIndex': 0, 'routeEdges': ['incoming', 'turn_exit'], 'vehicleClass': 'bus'}},
           'downstream': {'east': {'edgeId': 'turn_exit', 'occupancyPercent': 90, 'spillbackIndicator': True}}}
    assert controller.receiving_supply(raw, 'north') == 0
    raw['downstream']['east'].update(occupancyPercent=20, spillbackIndicator=False)
    assert controller.receiving_supply(raw, 'north') == pytest.approx(.8)
