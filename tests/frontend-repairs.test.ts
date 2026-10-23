import assert from 'node:assert/strict';
import { TrafficSimulationEngine } from '../src/simulation/engine';
import { ALL_25_SCENARIOS } from '../src/simulation/scenarios';
import { TrafficProviderService } from '../src/services/trafficProvider';

async function main() {
  const engine = new TrafficSimulationEngine();
  const original = ALL_25_SCENARIOS[0].arrivalRates.north;
  const custom = structuredClone(ALL_25_SCENARIOS[0]); custom.arrivalRates.north = 2350;
  engine.loadScenario(custom);
  assert.equal(engine.getState().scenario.arrivalRates.north, 2350);
  custom.arrivalRates.north = 0;
  assert.equal(engine.getState().scenario.arrivalRates.north, 2350);
  assert.equal(ALL_25_SCENARIOS[0].arrivalRates.north, original);
  engine.setSeed(0); assert.equal(engine.getSeed(), 0);
  console.log('PASS custom inflow persists, catalog isolated, seed0 accepted');

  const before = engine.getState().signals.pedestrianSignals.north.waitingCount;
  engine.requestPedestrianCall('north');
  assert.equal(engine.getState().signals.pedestrianSignals.north.waitingCount, before + 1);
  console.log('PASS pedestrian call reaches engine authority');
  engine.injectEmergency('north', 'ambulance');
  const alertIds = engine.getState().recentAlerts.map(alert => alert.id);
  assert.equal(new Set(alertIds).size, alertIds.length);
  console.log('PASS scenario and emergency alerts have unique identities');

  class FakeSocket {
    static OPEN = 1; static CONNECTING = 0;
    readyState = 1; onopen: any; onclose: any; onerror: any; onmessage: any;
    sent = ''; static last: FakeSocket;
    constructor(public url: string) { FakeSocket.last = this; }
    send(data: string) { this.sent = data; }
    close() { this.readyState = 3; }
  }
  const previousSocket = globalThis.WebSocket; const previousFetch = globalThis.fetch;
  (globalThis as any).WebSocket = FakeSocket;
  const provider = new TrafficProviderService();
  try {
    provider.setMode('remote_backend');
    let completed = false;
    const pending = provider.sendCommand({ commandId:'audit-ack',action:'STEP',timestamp:Date.now() }).then(ack => { completed=true; return ack; });
    await Promise.resolve(); assert.equal(completed,false,'dispatch is not acknowledgement');
    assert.equal(JSON.parse(FakeSocket.last.sent).data.commandId,'audit-ack');
    FakeSocket.last.onmessage({ data:JSON.stringify({type:'COMMAND_ACK',sequenceNumber:1,data:{commandId:'audit-ack',success:false,message:'Rejected by backend',executionTimestamp:Date.now()}}) });
    assert.equal((await pending).success,false);
    console.log('PASS remote command waits for genuine backend acknowledgement');
    FakeSocket.last.readyState = 3;
    globalThis.fetch = (async () => { throw new Error('offline'); }) as typeof fetch;
    const time = provider.getEngine().getState().simTime;
    const rejected = await provider.sendCommand({commandId:'audit-offline',action:'STEP',timestamp:Date.now()});
    assert.equal(rejected.success,false); assert.equal(provider.getEngine().getState().simTime,time);
    console.log('PASS remote failure does not silently mutate local simulation');
  } finally { provider.setMode('local_demo'); globalThis.WebSocket=previousSocket; globalThis.fetch=previousFetch; }
}
main().catch(error => { console.error(error);process.exitCode=1; });
