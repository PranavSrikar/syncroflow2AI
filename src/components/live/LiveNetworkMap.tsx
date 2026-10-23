import React, { memo, useMemo, useEffect, useRef, useState } from 'react';
import type { Snapshot } from '../views/SumoLiveView';
import { Badge } from './primitives';
type Raw = NonNullable<Snapshot['telemetry']>;
export const signalColor = (state: string) => state === 'G' ? '#62d5a3' : state === 'g' ? '#a8d692' : state.toLowerCase() === 'y' ? '#f2bd65' : state.toLowerCase() === 'r' ? '#ed8891' : '#8495ab';
export const LiveNetworkMap = memo(function LiveNetworkMap({ raw, online, junction }: { raw: Raw | null; online: boolean; junction: string }) {
  const geometry = raw?.networkGeometry;
  const host = useRef<HTMLDivElement>(null);
  const [aspect, setAspect] = useState(1.6);
  const [radius, setRadius] = useState(65);
  const [labels, setLabels] = useState(false);
  useEffect(() => {
    if (!host.current) return;
    const observer = new ResizeObserver(([entry]) => {
      const {width,height}=entry.contentRect;
      if(width && height) setAspect(width/Math.max(1,height-30));
    });
    observer.observe(host.current);
    return () => observer.disconnect();
  }, [!!geometry]);
  const bounds = useMemo(() => {
    if (!geometry) return null;
    // A selected signal's incoming lane endpoints define a local camera. In
    // network mode use every actual lane, preserving the connecting corridor.
    const light = raw?.trafficLights[junction];
    const node = geometry.junctions[junction];
    const points = Object.values(geometry.lanes).flatMap(lane => lane.shape);
    if (!points.length) return null;
    if (node && light && junction !== 'network') return [node.position[0]-radius*aspect, -node.position[1]-radius, 2*radius*aspect, 2*radius];
    const xs = points.map(p=>p[0]), ys = points.map(p=>-p[1]);
    const x = Math.min(...xs)-18, y = Math.min(...ys)-18;
    return [x,y,Math.max(...xs)-x+18,Math.max(...ys)-y+18];
  }, [geometry, junction, radius, aspect]);
  if (!raw || !geometry || !bounds) return <div className="sf-map-empty"><div className="sf-empty-cross" aria-hidden="true">＋</div><h3>{raw ? 'Map geometry unavailable' : 'Your network, ready to observe'}</h3><p>{raw ? 'Aggregate telemetry remains available below. No vehicle positions are invented.' : 'Choose a network and controller below, then Start to reveal real SUMO roads, signals and vehicle positions.'}</p><Badge>SUMO / TraCI · exact observed coordinates</Badge></div>;
  const [x,y,w,h] = bounds;
  const vehicles = Object.entries(raw.vehicleDetails ?? {}).filter(([,v]) => v.position[0] >= x && v.position[0] <= x+w && -v.position[1] >= y && -v.position[1] <= y+h);
  // Bound DOM work on very large networks. Omitted positions are disclosed.
  const visible = vehicles.slice(0, 1500);
  const crossingLanes = new Set(raw.pedestrianSignals.map(c=>c.outgoingLane));
  return <div className="sf-map-wrap" ref={host}>
    <div className="sf-map-overlay"><Badge tone={online ? 'good' : 'warn'}>{online ? 'Observed positions' : 'Stale positions'}</Badge><span>{raw.simTime.toFixed(0)} s · {vehicles.length} vehicles in view</span></div>
    <svg className="sf-network-map" role="img" aria-label="Live SUMO digital twin" viewBox={bounds.join(' ')} data-sim-time={raw.simTime}>
      <title>Actual SUMO lane geometry, observed vehicle positions and controlled signal links. North is up; coordinates in metres.</title>
      <defs><pattern id="world-grid" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M 20 0 L 0 0 0 20" fill="none" stroke="#1c2b3a" strokeWidth="0.25" /></pattern><marker id="lane-direction" markerWidth="3" markerHeight="3" refX="2" refY="1.5" orient="auto"><path d="M0 0 L3 1.5 L0 3" fill="#8ba7b8" /></marker></defs>
      <rect x={x} y={y} width={w} height={h} fill="#0b1b25" /><rect x={x} y={y} width={w} height={h} fill="url(#world-grid)" />
      {Object.entries(geometry.lanes).filter(([id])=>!id.startsWith(':')).map(([id,lane])=><polyline key={id} points={lane.shape.map(p=>`${p[0]},${-p[1]}`).join(' ')} fill="none" stroke="#42505e" strokeWidth={lane.width+1.1} />)}
      {Object.entries(geometry.junctions).filter(([,j])=>j.shape.length>2).map(([id,j])=><polygon key={id} points={j.shape.map(p=>`${p[0]},${-p[1]}`).join(' ')} fill="#263643" stroke="#50606d" strokeWidth=".3" />)}
      {Object.entries(geometry.lanes).map(([id,lane])=><g key={id}><polyline points={lane.shape.map(p=>`${p[0]},${-p[1]}`).join(' ')} fill="none" stroke={crossingLanes.has(id) ? '#a1aaa8' : '#263846'} strokeWidth={crossingLanes.has(id)?Math.max(.5,lane.width-.4):lane.width} strokeDasharray={crossingLanes.has(id)?'0.6 0.6':undefined} strokeLinecap="butt" /><polyline points={lane.shape.map(p=>`${p[0]},${-p[1]}`).join(' ')} fill="none" stroke="#c5c8b9" strokeOpacity="0.4" strokeWidth="0.12" strokeDasharray="2 3" /></g>)}
      {Object.entries(geometry.lanes).filter(([id,l])=>!id.startsWith(':') && l.shape.length>=2).map(([id,lane])=>{
        const a=lane.shape.at(-2)!,b=lane.shape.at(-1)!;const length=Math.hypot(b[0]-a[0],b[1]-a[1]);if(length<12)return null;
        const point=(distance:number)=>[b[0]-(b[0]-a[0])*distance/length,-b[1]+(b[1]-a[1])*distance/length];
        const p=point(10),q=point(6);return <line key={id} x1={p[0]} y1={p[1]} x2={q[0]} y2={q[1]} stroke="#8ba7b8" strokeWidth=".35" markerEnd="url(#lane-direction)"><title>{id}: lane travel direction</title></line>;
      })}
      {Object.entries(raw.trafficLights).flatMap(([id,light]) => (light.controlledLinks ?? []).flatMap((group,index)=>group.map((link,i)=>{
        const end = geometry.lanes[link[0]]?.shape.at(-1); if (!end) return null;
        return <circle key={`${id}-${index}-${i}`} cx={end[0]} cy={-end[1]} r="1" fill={signalColor(light.signalState[index])} stroke="#0a111c" strokeWidth="0.35" data-signal-id={`${id}-${index}`} data-state={light.signalState[index]}><title>{id} link {index}: {light.signalState[index]} · {link[0]} → {link[1]}</title></circle>;
      })))}
      {visible.map(([id,v])=>{
        // SUMO position is the front bumper; heading clockwise from north.
        const emergency = v.vehicleClass === 'emergency';
        return <g key={id} transform={`translate(${v.position[0]} ${-v.position[1]}) rotate(${v.angle})`} data-vehicle-id={id} data-world-x={v.position[0]} data-world-y={v.position[1]}><title>{id} · {v.vehicleClass} / {v.typeId} · {v.speedMps.toFixed(1)} m/s</title><rect x={-v.vehicleWidth/2} y="0" width={v.vehicleWidth} height={v.vehicleLength} rx="0.45" fill={emergency ? '#f2838d' : v.speedMps < 0.1 ? '#e5b970' : ['bus','truck','trailer'].includes(v.vehicleClass) ? '#94a8cf' : '#65c7c4'} stroke={emergency ? '#ffd2d6' : '#07131b'} strokeWidth={emergency ? '0.6' : '0.2'} /><path d={`M ${-v.vehicleWidth/3} 1.2 h ${v.vehicleWidth*2/3}`} stroke="#0b2632" strokeWidth="0.7" /></g>;
      })}
      {Object.entries(raw.pedestrians).map(([id,p])=>p.position && <circle key={id} cx={p.position[0]} cy={-p.position[1]} r="0.65" fill="#f3dda0"><title>Pedestrian {id} · waiting {p.waitingTimeSec.toFixed(0)} s</title></circle>)}
      {Object.entries(raw.trafficLights).map(([id,light])=>{
        const node=geometry.junctions[id]; return node && <text key={id} x={node.position[0]+13} y={-node.position[1]-14} fill="#b6cadb" fontSize="3" fontFamily="monospace">{id} · P{light.phaseIndex}</text>;
      })}
      {labels && Object.entries(geometry.lanes).filter(([id,l])=>!id.startsWith(':') && l.shape.length>1).map(([id,l])=>{const p=l.shape[Math.floor(l.shape.length/2)];return <text key={id} x={p[0]} y={-p[1]} fill="#afc9cf" fontSize="2.3">{l.edgeId}</text>})}
    </svg>
    <div className="sf-map-tools"><button className="sf-map-tool-label" aria-pressed={labels} onClick={()=>setLabels(!labels)}>Road IDs</button><button aria-label="Zoom in digital twin" title={junction==='network'?'Select a junction to zoom':'Zoom in; positions remain observed'} disabled={junction==='network' || radius<=35} onClick={()=>setRadius(r=>Math.max(35,r-15))}>+</button><button aria-label="Zoom out digital twin" title="Zoom out" disabled={junction==='network' || radius>=185} onClick={()=>setRadius(r=>Math.min(185,r+15))}>−</button></div>
    <div className="sf-map-legend"><span><i style={{background:'#65c7c4'}} /> Moving</span><span><i style={{background:'#e5b970'}} /> Halted &lt; 0.1 m/s</span><span><i style={{background:'#f2838d'}} /> Emergency</span><span>N ↑ · metres</span></div>
    {vehicles.length > 1500 && <p className="sf-caption">Showing first 1,500 of {vehicles.length} observed vehicles. Counts include all vehicles.</p>}
  </div>;
});
