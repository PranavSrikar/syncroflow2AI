"""
SYNCHROFLOW AI — Scenario Catalog & Activation Routes
Supports all 25 canonical scenarios defined in the frontend.
"""

import time
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.simulation_service import simulation_service
from app.schemas.commands import CommandPayload, CommandAckResponse

router = APIRouter(prefix="/api/v1/scenarios", tags=["scenarios"])

# Predefined 25 scenarios metadata
CANONICAL_25_SCENARIOS = [
    {"numericId": 1, "id": "balanced_traffic", "name": "Balanced Baseline Traffic", "category": "baseline"},
    {"numericId": 2, "id": "peak_morning_commute", "name": "Peak Morning Commute (NS Heavy)", "category": "rush_hour"},
    {"numericId": 3, "id": "evening_rush_ew", "name": "Evening Rush (EW Dominant)", "category": "rush_hour"},
    {"numericId": 4, "id": "friday_evening_gridlock", "name": "Friday Evening Near-Saturation", "category": "rush_hour"},
    {"numericId": 5, "id": "dense_fog_visibility", "name": "Dense Fog & Reduced Visibility", "category": "weather"},
    {"numericId": 6, "id": "monsoon_deluge", "name": "Monsoon Deluge (Low Friction)", "category": "weather"},
    {"numericId": 7, "id": "heterogeneous_mix", "name": "High Heterogeneity (Bikes & Rickshaws)", "category": "multimodal"},
    {"numericId": 8, "id": "freight_corridor_trucks", "name": "Heavy Freight & Logistics Corridor", "category": "multimodal"},
    {"numericId": 9, "id": "night_low_demand", "name": "Low-Demand Night Quiescence", "category": "baseline"},
    {"numericId": 10, "id": "stadium_surge", "name": "Stadium Event Post-Game Surge", "category": "surge"},
    {"numericId": 11, "id": "ambulance_priority_north", "name": "North Corridor Ambulance Priority", "category": "emergency"},
    {"numericId": 12, "id": "dual_emergency_conflict", "name": "Dual Conflicting Emergency Vehicles", "category": "emergency"},
    {"numericId": 13, "id": "breakdown_lane_block", "name": "Stalled Vehicle Lane Blockage", "category": "incident"},
    {"numericId": 14, "id": "left_turn_spillback", "name": "Severe Left-Turn Pocket Spillback", "category": "spillback"},
    {"numericId": 15, "id": "downstream_bottleneck", "name": "Downstream Exit Blockage Shockwave", "category": "spillback"},
    {"numericId": 16, "id": "pedestrian_scramble_surge", "name": "Active Mobility Pedestrian Surge", "category": "multimodal"},
    {"numericId": 17, "id": "rainstorm_night", "name": "Nocturnal Rainstorm Influx", "category": "weather"},
    {"numericId": 18, "id": "construction_lane_drop", "name": "Construction Work Zone Lane Drop", "category": "incident"},
    {"numericId": 19, "id": "vip_motorcade_corridor", "name": "VIP Motorcade Green Wave", "category": "special"},
    {"numericId": 20, "id": "sensor_camera_occlusion", "name": "Sensor Fault & Camera Occlusion", "category": "degradation"},
    {"numericId": 21, "id": "high_speed_speeding", "name": "Aggressive High-Speed Vehicles", "category": "safety"},
    {"numericId": 22, "id": "bus_rapid_transit_bunching", "name": "Transit Bus Bunching Corridor", "category": "multimodal"},
    {"numericId": 23, "id": "pothole_swerving_erratic", "name": "Pothole Swerving Lateral Shift", "category": "safety"},
    {"numericId": 24, "id": "connected_autonomous_fleet", "name": "Autonomous Vehicle (V2X) Fleet", "category": "special"},
    {"numericId": 25, "id": "full_stress_gridlock", "name": "Multi-Factor Stress Gridlock", "category": "stress"},
]


@router.get("")
@router.get("/")
async def list_scenarios():
    return {
        "count": len(CANONICAL_25_SCENARIOS),
        "scenarios": CANONICAL_25_SCENARIOS,
        "activeScenarioId": simulation_service.scenario_id,
    }


@router.post("/{scenario_id}/load", response_model=CommandAckResponse)
async def load_scenario(scenario_id: str):
    found = any(s["id"] == scenario_id for s in CANONICAL_25_SCENARIOS)
    if not found:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found in canonical catalog")

    cmd = CommandPayload(
        commandId=f"cmd-load-sc-{int(time.time()*1000)}",
        action="LOAD_SCENARIO",
        timestamp=int(time.time() * 1000),
        payload={"scenarioId": scenario_id},
    )
    return simulation_service.handle_command(cmd)
