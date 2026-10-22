"""
Unit tests for Python Simulation Engine:
Determinism, PRNG seed repeatability, safety interlock clearance, and emergency preemption.
"""

import pytest
from app.services.simulation_service import SimulationService, SeededPRNG


def test_prng_determinism():
    prng1 = SeededPRNG(4242)
    prng2 = SeededPRNG(4242)
    seq1 = [prng1.next() for _ in range(30)]
    seq2 = [prng2.next() for _ in range(30)]
    assert seq1 == seq2, "Identical seeds must yield bit-identical sequence"

    prng1.reset()
    seq1_reset = [prng1.next() for _ in range(30)]
    assert seq1 == seq1_reset, "PRNG reset must reproduce initial sequence"


def test_simulation_service_determinism():
    simA = SimulationService(seed=777)
    simB = SimulationService(seed=777)

    for _ in range(50):
        simA.step(0.5)
        simB.step(0.5)

    stateA = simA.get_state_payload()
    stateB = simB.get_state_payload()

    assert len(stateA.vehicles) == len(stateB.vehicles), "Vehicle counts must match exactly"
    assert stateA.metrics.totalVehiclesSpawned == stateB.metrics.totalVehiclesSpawned
    assert stateA.simTime == stateB.simTime


def test_conflict_matrix_invariants():
    sim = SimulationService(seed=123)

    # Step through 200 cycles and check that NS and EW are never simultaneously green
    for _ in range(200):
        sim.step(0.5)
        apps = sim.signals.approachSignals
        ns_green = (apps["north"].through == "green") or (apps["south"].through == "green")
        ew_green = (apps["east"].through == "green") or (apps["west"].through == "green")
        assert not (ns_green and ew_green), "NS and EW conflicting movements must NEVER be green simultaneously"


def test_clearance_stages_traversal():
    sim = SimulationService(seed=999)
    saw_yellow = False
    saw_all_red = False

    for _ in range(120):
        sim.step(0.5)
        stg = sim.signals.transitionStage
        if stg == "YELLOW_CLEARANCE":
            saw_yellow = True
        elif stg == "ALL_RED_CLEARANCE":
            saw_all_red = True

    assert saw_yellow, "Engine must traverse explicit YELLOW_CLEARANCE"
    assert saw_all_red, "Engine must traverse explicit ALL_RED_CLEARANCE"


def test_emergency_preemption_handling():
    sim = SimulationService(seed=555)
    emerg_veh = sim.inject_emergency("north", "ambulance")

    assert emerg_veh.isEmergency is True
    assert sim.signals.isPreemptActive is True
    assert sim.signals.transitionStage == "YELLOW_CLEARANCE", "Emergency injection must trigger safe clearance"
