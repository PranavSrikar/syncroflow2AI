import type { Snapshot } from '../components/views/SumoLiveView';
export type TrafficObservation = NonNullable<Snapshot['telemetry']>;
export function approachPermission(raw: TrafficObservation, direction: string) {
  const edge = raw.approaches[direction]?.edgeId;
  if (!edge) return { label: 'Not reported', states: '', tone: 'neutral' };
  const states = [...new Set(Object.values(raw.trafficLights).flatMap(light => (light.controlledLinks ?? []).flatMap((links, index) => links.some(link => link[0].startsWith(edge + '_')) ? [light.signalState[index]] : [])))].filter(Boolean);
  const green = states.some(s => s === 'G' || s === 'g');
  return { states: states.join(''), label: !states.length ? 'Not reported' : green ? states.every(s => s === 'G' || s === 'g') ? 'Green' : 'Partial green' : states.some(s => s.toLowerCase() === 'y') ? 'Clearance' : states.every(s => s === 'r') ? 'Stop' : 'Other permission', tone: green ? 'good' : states.includes('y') ? 'warn' : 'neutral' };
}
export function policySummary(policy: unknown) {
  switch (policy) {
    case 'constrained_mpc': return 'MPC selected a feasible timing candidate.';
    case 'max_pressure_fallback': return 'Max-Pressure fallback is active. MPC did not produce an available candidate.';
    case 'emergency_priority': return 'Emergency priority requested supervised timing.';
    case 'phase_expiry_pending': return 'The approved phase is due to switch. Its scheduled transition is retained.';
    case 'Extend incumbent when its pressure dominates; retain legal cyclic service': return 'The controller evaluated queue pressure within the approved cyclic programme.';
    case undefined: case null: case '': return 'No adaptive decision reported yet.';
    default: return 'The backend reported a policy. Inspect its exact trace for details.';
  }
}
