"""
Integration tests for FastAPI REST Endpoints:
Verifies HTTP status codes, schema validity, and state updates across all Phase A routes.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["protocolVersion"] == "v1.2.0"
    assert "serverTime" in data


def test_capabilities_endpoint():
    response = client.get("/api/v1/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert data["protocolVersion"] == "v1.2.0"
    assert len(data["supportedControllers"]) == 7
    assert data["supportedScenarios"] == 25


def test_simulation_state_and_lifecycle():
    # 1. State retrieval
    res_state = client.get("/api/v1/simulation/state")
    assert res_state.status_code == 200
    state = res_state.json()
    assert state["protocolVersion"] == "v1.2.0"
    assert "signals" in state
    assert "metrics" in state
    assert "telemetry" in state

    # 2. Pause
    res_pause = client.post("/api/v1/simulation/pause")
    assert res_pause.status_code == 200
    assert res_pause.json()["success"] is True

    # 3. Resume
    res_start = client.post("/api/v1/simulation/start")
    assert res_start.status_code == 200
    assert res_start.json()["success"] is True

    # 4. Step
    res_step = client.post("/api/v1/simulation/step")
    assert res_step.status_code == 200
    assert res_step.json()["success"] is True


def test_scenarios_endpoints():
    res_list = client.get("/api/v1/scenarios")
    assert res_list.status_code == 200
    scenarios = res_list.json()["scenarios"]
    assert len(scenarios) == 25

    # Load monsoon scenario
    res_load = client.post("/api/v1/scenarios/monsoon_deluge/load")
    assert res_load.status_code == 200
    assert res_load.json()["success"] is True


def test_controllers_endpoints():
    res_list = client.get("/api/v1/controllers")
    assert res_list.status_code == 200
    ctrls = res_list.json()["controllers"]
    assert len(ctrls) == 7

    # Select Max-Pressure
    res_select = client.post("/api/v1/controllers/max_pressure/select")
    assert res_select.status_code == 200
    assert res_select.json()["success"] is True


def test_emergency_preemption_endpoint():
    res_inject = client.post(
        "/api/v1/emergencies/inject",
        json={"direction": "north", "type": "ambulance"},
    )
    assert res_inject.status_code == 200
    assert res_inject.json()["success"] is True

    res_status = client.get("/api/v1/emergencies/status")
    assert res_status.status_code == 200
    assert res_status.json()["isPreemptActive"] is True


def test_benchmark_runner_endpoint():
    req = {
        "scenarioId": "balanced_traffic",
        "seed": 42,
        "durationSec": 10,
        "controllers": ["fixed", "max_pressure"],
    }
    res_bench = client.post("/api/v1/benchmarks/run", json=req)
    assert res_bench.status_code == 200
    data = res_bench.json()
    assert data["seed"] == 42
    assert len(data["results"]) == 2
    assert data["results"][0]["controller"] == "fixed"
