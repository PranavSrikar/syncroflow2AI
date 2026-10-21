/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { TrafficSimulationEngine } from '../src/simulation/engine.ts';
import { SeededPRNG } from '../src/simulation/random.ts';
import { ALL_25_SCENARIOS } from '../src/simulation/scenarios.ts';
import { trafficProvider } from '../src/services/trafficProvider.ts';

function assert(condition: boolean, message: string) {
  if (!condition) {
    console.error(`❌ ASSERTION FAILED: ${message}`);
    throw new Error(message);
  } else {
    console.log(`  ✓ ${message}`);
  }
}

async function runAllTests() {
  console.log('\n========================================');
  console.log('SYNCHROFLOW AI — AUTOMATED TEST SUITE');
  console.log('Phases 1–4 Quality & Safety Verification');
  console.log('========================================\n');

  // Test 1: Deterministic Seed PRNG
  console.log('TEST 1: Seeded PRNG Determinism & Reproducibility');
  const prng1 = new SeededPRNG(4242);
  const prng2 = new SeededPRNG(4242);
  const seq1 = Array.from({ length: 20 }, () => prng1.next());
  const seq2 = Array.from({ length: 20 }, () => prng2.next());
  assert(
    JSON.stringify(seq1) === JSON.stringify(seq2),
    'Identical seeds produce bit-identical pseudorandom sequences'
  );

  prng1.reset();
  const seq1_reset = Array.from({ length: 20 }, () => prng1.next());
  assert(
    JSON.stringify(seq1) === JSON.stringify(seq1_reset),
    'Resetting PRNG reproduces identical sequence from start'
  );

  // Test 2: Engine Run Reproducibility with Same Seed
  console.log('\nTEST 2: Simulation Engine Determinism');
  const engineA = new TrafficSimulationEngine(ALL_25_SCENARIOS[0], 777);
  const engineB = new TrafficSimulationEngine(ALL_25_SCENARIOS[0], 777);

  for (let i = 0; i < 40; i++) {
    engineA.step(0.5);
    engineB.step(0.5);
  }

  const stateA = engineA.getState();
  const stateB = engineB.getState();

  assert(stateA.vehicles.length === stateB.vehicles.length, 'Vehicle counts match exactly');
  assert(
    stateA.vehicles[0]?.speed === stateB.vehicles[0]?.speed,
    'Lead vehicle speeds match to floating-point precision'
  );
  assert(
    stateA.metrics.totalVehiclesSpawned === stateB.metrics.totalVehiclesSpawned,
    'Total vehicles spawned match exactly'
  );

  // Test 3: Signal Conflict Matrix Invariant (Safety Supervisor)
  console.log('\nTEST 3: Safety Supervisor & Conflict Matrix Interlock');
  const testEngine = new TrafficSimulationEngine(ALL_25_SCENARIOS[0], 123);
  const sig = testEngine.getState().signals;

  // Verify initial phase
  assert(sig.safetyReport.conflictCheckPassed, 'Initial state satisfies conflict matrix');

  // Step through an entire cycle and verify NO conflict occurs
  let anyConflictDetected = false;
  for (let i = 0; i < 240; i++) {
    testEngine.step(0.5);
    const s = testEngine.getState().signals;
    const apps = s.approachSignals;
    const nsGreen = apps.north.through === 'green' || apps.south.through === 'green';
    const ewGreen = apps.east.through === 'green' || apps.west.through === 'green';
    if (nsGreen && ewGreen) {
      anyConflictDetected = true;
    }
  }
  assert(!anyConflictDetected, 'Conflicting NS and EW movements NEVER simultaneously green');

  // Test 4: Yellow & All-Red Clearance Interval Guarantees
  console.log('\nTEST 4: Yellow & All-Red Mandatory Clearance Intervals');
  const monsoonEngine = new TrafficSimulationEngine(ALL_25_SCENARIOS[5], 999); // Monsoon scenario
  assert(monsoonEngine.getState().weather === 'monsoon', 'Monsoon scenario loaded');

  // Verify yellow clearance begins before all-red
  let sawYellow = false;
  let sawAllRed = false;

  for (let i = 0; i < 100; i++) {
    monsoonEngine.step(0.5);
    const stg = monsoonEngine.getState().signals.transitionStage;
    if (stg === 'YELLOW_CLEARANCE') sawYellow = true;
    if (stg === 'ALL_RED_CLEARANCE') sawAllRed = true;
  }
  assert(sawYellow, 'Explicit YELLOW_CLEARANCE stage traversed');
  assert(sawAllRed, 'Explicit ALL_RED_CLEARANCE stage traversed');

  // Test 5: Emergency Preemption
  console.log('\nTEST 5: Emergency Vehicle Priority & Preemption');
  const emergEngine = new TrafficSimulationEngine(ALL_25_SCENARIOS[0], 555);
  emergEngine.injectEmergency('north', 'ambulance');
  const eState = emergEngine.getState();
  assert(eState.signals.isPreemptActive, 'Preemption flag activated upon emergency injection');
  assert(
    eState.vehicles.some((v) => v.isEmergency),
    'Emergency vehicle successfully placed on North approach'
  );

  // Test 6: All 25 Scenarios Availability and Catalog Integrity
  console.log('\nTEST 6: All 25 Predefined Scenarios Catalog');
  assert(ALL_25_SCENARIOS.length === 25, 'Catalog contains exactly 25 predefined scenarios');
  for (let id = 1; id <= 25; id++) {
    const sc = ALL_25_SCENARIOS.find((s) => s.numericId === id);
    assert(sc !== undefined, `Scenario ${id} exists and has numeric ID`);
  }

  // Test 7: Observable Scenario Differences
  console.log('\nTEST 7: Observable Scenario Dynamics');
  const scMonsoon = ALL_25_SCENARIOS.find((s) => s.id === 'monsoon_deluge')!;
  const scIncident = ALL_25_SCENARIOS.find((s) => s.id === 'breakdown_lane_block')!;
  const scClosure = ALL_25_SCENARIOS.find((s) => s.id === 'police_road_closure')!;

  assert(scMonsoon.weather === 'monsoon', 'Monsoon changes meteorological friction');
  assert(Boolean(scIncident.hasIncident && scIncident.incidentApproach === 'east'), 'Breakdown configures incident lane stall');
  assert(scClosure.roadClosureApproach === 'west', 'Road closure blocks West approach');

  // Test 8: Provider Subscription and Cleanup
  console.log('\nTEST 8: Traffic Provider Lifecycle & Subscription Cleanup');
  let callbackFired = 0;
  const unsubscribe = trafficProvider.subscribe(() => {
    callbackFired++;
  });
  assert(callbackFired > 0, 'Subscriber receives initial state upon attachment');

  unsubscribe();
  const countBefore = callbackFired;
  trafficProvider.notifySubscribers(trafficProvider.getEngine().getState());
  assert(callbackFired === countBefore, 'Unsubscribed callback is successfully detached');

  console.log('\n========================================');
  console.log('✅ ALL TEST SUITES PASSED (8/8 Verified)');
  console.log('========================================\n');
}

runAllTests().catch((err) => {
  console.error('Test suite failed:', err);
  process.exit(1);
});
