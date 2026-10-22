/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import {
  Direction,
  MovementType,
  Vehicle,
  WeatherMode,
  CameraViewPreset,
  IntersectionSignalState,
} from '../../types/traffic.ts';
import { buildIntersectionScene, updateSignalLensColors, TrafficSignalMeshGroup } from './cityBuilder.ts';
import { buildProceduralVehicle } from './vehicleBuilder.ts';
import { APPROACH_LENGTH, INTERSECTION_RADIUS, LANE_WIDTH } from '../../simulation/engine.ts';

interface TrafficSceneProps {
  vehicles: Vehicle[];
  signals: IntersectionSignalState;
  weather: WeatherMode;
  cameraPreset: CameraViewPreset;
  showAnalyticsOverlay?: boolean;
  showSensorOverlays?: boolean;
  onVehicleClick?: (vehicle: Vehicle) => void;
}

// Pre-allocated math objects to ensure zero GC during frame updates
const _vec3 = new THREE.Vector3();
const _targetPos = new THREE.Vector3();
const _camPos = new THREE.Vector3();

export const TrafficScene: React.FC<TrafficSceneProps> = ({
  vehicles,
  signals,
  weather,
  cameraPreset,
  showAnalyticsOverlay = true,
  showSensorOverlays = true,
}) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const signalsRef = useRef<Record<Direction, TrafficSignalMeshGroup> | null>(null);

  // Cached vehicle groups mapped by vehicle id
  const vehicleMeshesRef = useRef<Map<string, THREE.Group>>(new Map());
  const rainSystemRef = useRef<THREE.Points | null>(null);
  const dirLightRef = useRef<THREE.DirectionalLight | null>(null);
  const hemiLightRef = useRef<THREE.HemisphereLight | null>(null);
  const trajectoryGroupRef = useRef<THREE.Group | null>(null);
  const sensorFrustumsRef = useRef<THREE.Group | null>(null);

  // Keep references to latest props for animation loop
  const vehiclesPropRef = useRef(vehicles);
  vehiclesPropRef.current = vehicles;

  const signalsPropRef = useRef(signals);
  signalsPropRef.current = signals;

  const weatherPropRef = useRef(weather);
  weatherPropRef.current = weather;

  const cameraPresetPropRef = useRef(cameraPreset);
  cameraPresetPropRef.current = cameraPreset;

  useEffect(() => {
    if (!mountRef.current) return;
    const container = mountRef.current;
    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || window.innerHeight;

    // Detect software WebGL safely
    const isSoftwareGl = (() => {
      const gl = document.createElement('canvas').getContext('webgl2');
      if (!gl) return true;
      const ext = gl.getExtension('WEBGL_debug_renderer_info');
      const param = ext ? ext.UNMASKED_RENDERER_WEBGL : gl.RENDERER;
      const gpu = String(gl.getParameter(param));
      gl.getExtension('WEBGL_lose_context')?.loseContext();
      return /SwiftShader|llvmpipe|softpipe|Software|Basic Render/i.test(gpu);
    })();

    // Initialize Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0f18);
    scene.fog = new THREE.FogExp2(0x0a0f18, 0.006);
    sceneRef.current = scene;

    // Camera
    const camera = new THREE.PerspectiveCamera(42, width / height, 0.5, 600);
    camera.position.set(0, 95, 42);
    cameraRef.current = camera;

    // Renderer
    const renderer = new THREE.WebGLRenderer({
      antialias: !isSoftwareGl,
      powerPreference: 'high-performance',
      alpha: false,
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(isSoftwareGl ? 1 : Math.min(window.devicePixelRatio, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;
    renderer.shadowMap.enabled = !isSoftwareGl;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Procedural Studio Environment Reflection
    const pmremGenerator = new THREE.PMREMGenerator(renderer);
    scene.environment = pmremGenerator.fromScene(new RoomEnvironment(), 0.04).texture;
    pmremGenerator.dispose();

    // Orbit Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = !isSoftwareGl;
    controls.dampingFactor = 0.08;
    controls.maxPolarAngle = Math.PI / 2 - 0.05; // Do not go below ground
    controls.minDistance = 15;
    controls.maxDistance = 180;
    controls.target.set(0, 1, 0);
    controlsRef.current = controls;

    // Studio Lighting Rig
    const hemiLight = new THREE.HemisphereLight(0x7dd3fc, 0x1e293b, 1.2);
    hemiLight.position.set(0, 50, 0);
    scene.add(hemiLight);
    hemiLightRef.current = hemiLight;

    const dirLight = new THREE.DirectionalLight(0xfff8db, 2.4);
    dirLight.position.set(45, 80, 55);
    dirLight.castShadow = !isSoftwareGl;
    dirLight.shadow.mapSize.width = 2048;
    dirLight.shadow.mapSize.height = 2048;
    dirLight.shadow.camera.near = 10;
    dirLight.shadow.camera.far = 250;
    const d = 60;
    dirLight.shadow.camera.left = -d;
    dirLight.shadow.camera.right = d;
    dirLight.shadow.camera.top = d;
    dirLight.shadow.camera.bottom = -d;
    dirLight.shadow.bias = -0.0004;
    scene.add(dirLight);
    dirLightRef.current = dirLight;

    // Ambient Fill Light
    const fillLight = new THREE.DirectionalLight(0x38bdf8, 0.8);
    fillLight.position.set(-45, 40, -55);
    scene.add(fillLight);

    // Build City & Traffic Signals
    const { cityGroup, signals: signalMeshes } = buildIntersectionScene();
    scene.add(cityGroup);
    signalsRef.current = signalMeshes;

    // Trajectory Overlays Group
    const trajectoryGroup = new THREE.Group();
    scene.add(trajectoryGroup);
    trajectoryGroupRef.current = trajectoryGroup;

    // Sensor Frustums Group
    const sensorGroup = new THREE.Group();
    scene.add(sensorGroup);
    sensorFrustumsRef.current = sensorGroup;
    buildSensorOverlays(sensorGroup);

    // Rain Particle System for Monsoon
    const rainCount = 2400;
    const rainGeo = new THREE.BufferGeometry();
    const rainPositions = new Float32Array(rainCount * 3);
    for (let i = 0; i < rainCount; i++) {
      rainPositions[i * 3] = (Math.random() - 0.5) * 160;
      rainPositions[i * 3 + 1] = Math.random() * 60;
      rainPositions[i * 3 + 2] = (Math.random() - 0.5) * 160;
    }
    rainGeo.setAttribute('position', new THREE.BufferAttribute(rainPositions, 3));
    const rainMat = new THREE.PointsMaterial({
      color: 0x93c5fd,
      size: 0.35,
      transparent: true,
      opacity: 0.65,
    });
    const rainSystem = new THREE.Points(rainGeo, rainMat);
    rainSystem.visible = false;
    scene.add(rainSystem);
    rainSystemRef.current = rainSystem;

    // Animation Loop
    let animId = 0;
    let lastTime = performance.now();

    const animate = (time: number) => {
      animId = requestAnimationFrame(animate);
      const dt = Math.min(0.05, (time - lastTime) / 1000);
      lastTime = time;

      // Update Camera based on Preset
      updateCameraInterpolation(camera, controls, cameraPresetPropRef.current, dt, vehiclesPropRef.current);

      // Update Environmental Atmosphere
      updateEnvironment(weatherPropRef.current, scene, dirLightRef.current, hemiLightRef.current, rainSystemRef.current, dt);

      // Update Signal Light Heads
      if (signalsRef.current && signalsPropRef.current) {
        const sig = signalsPropRef.current.approachSignals;
        updateSignalLensColors(signalsRef.current.north, sig.north.through, sig.north.left);
        updateSignalLensColors(signalsRef.current.south, sig.south.through, sig.south.left);
        updateSignalLensColors(signalsRef.current.east, sig.east.through, sig.east.left);
        updateSignalLensColors(signalsRef.current.west, sig.west.through, sig.west.left);
      }

      // Update 3D Vehicles
      updateVehicles(scene, vehicleMeshesRef.current, vehiclesPropRef.current, dt);

      // Update Dynamic Trajectory Ribbons
      if (trajectoryGroupRef.current) {
        updateTrajectoryRibbons(trajectoryGroupRef.current, signalsPropRef.current, showAnalyticsOverlay);
      }

      controls.update();
      renderer.render(scene, camera);
    };

    animId = requestAnimationFrame(animate);

    // Resize Observer
    const handleResize = () => {
      if (!mountRef.current || !renderer || !camera) return;
      const w = mountRef.current.clientWidth;
      const h = mountRef.current.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  return (
    <div className="relative w-full h-full min-h-[480px] bg-slate-950 overflow-hidden select-none">
      <div ref={mountRef} className="absolute inset-0 w-full h-full" />
    </div>
  );
};

// Build Translucent Sensor Overlays (Cameras & LiDAR sensing cones)
function buildSensorOverlays(group: THREE.Group) {
  const coneGeo = new THREE.ConeGeometry(8, 22, 16, 1, true);
  const sensorMat = new THREE.MeshBasicMaterial({
    color: 0x00f2fe,
    transparent: true,
    opacity: 0.08,
    wireframe: true,
  });

  const sensorSpots = [
    { x: 12.2, y: 6.2, z: -17.5, rotX: Math.PI * 0.65, rotY: 0 },
    { x: -12.2, y: 6.2, z: 17.5, rotX: -Math.PI * 0.65, rotY: Math.PI },
    { x: 17.5, y: 6.2, z: 12.2, rotX: 0, rotZ: -Math.PI * 0.65 },
    { x: -17.5, y: 6.2, z: -12.2, rotX: 0, rotZ: Math.PI * 0.65 },
  ];

  sensorSpots.forEach((s) => {
    const mesh = new THREE.Mesh(coneGeo, sensorMat);
    mesh.position.set(s.x, s.y, s.z);
    if (s.rotX) mesh.rotation.x = s.rotX;
    if (s.rotY) mesh.rotation.y = s.rotY;
    if (s.rotZ) mesh.rotation.z = s.rotZ;
    group.add(mesh);
  });
}

// Update Trajectory Ribbons based on current open phase
function updateTrajectoryRibbons(group: THREE.Group, signals: IntersectionSignalState, isVisible: boolean) {
  if (!isVisible) {
    group.visible = false;
    return;
  }
  group.visible = true;

  // Clear previous ribbon children
  while (group.children.length > 0) {
    const child = group.children[0] as THREE.Mesh;
    group.remove(child);
    if (child.geometry) child.geometry.dispose();
  }

  const phase = signals.currentPhaseIndex;
  const greenMat = new THREE.MeshBasicMaterial({
    color: 0x10b981,
    transparent: true,
    opacity: 0.45,
    side: THREE.DoubleSide,
    depthWrite: false,
  });

  // Curve generators for active flow paths
  if (phase === 0) {
    // NS Through & Right
    createCurvedRibbon(group, [new THREE.Vector3(5.4, 0.08, -18), new THREE.Vector3(5.4, 0.08, 18)], greenMat);
    createCurvedRibbon(group, [new THREE.Vector3(-5.4, 0.08, 18), new THREE.Vector3(-5.4, 0.08, -18)], greenMat);
    // Right turns
    createCurvedRibbon(group, [new THREE.Vector3(9.0, 0.08, -18), new THREE.Vector3(12.0, 0.08, -12), new THREE.Vector3(18, 0.08, -9.0)], greenMat);
    createCurvedRibbon(group, [new THREE.Vector3(-9.0, 0.08, 18), new THREE.Vector3(-12.0, 0.08, 12), new THREE.Vector3(-18, 0.08, 9.0)], greenMat);
  } else if (phase === 1) {
    // NS Protected Left
    createCurvedRibbon(group, [new THREE.Vector3(1.8, 0.08, -18), new THREE.Vector3(1.8, 0.08, -4), new THREE.Vector3(-8, 0.08, -1.8), new THREE.Vector3(-18, 0.08, -1.8)], greenMat);
    createCurvedRibbon(group, [new THREE.Vector3(-1.8, 0.08, 18), new THREE.Vector3(-1.8, 0.08, 4), new THREE.Vector3(8, 0.08, 1.8), new THREE.Vector3(18, 0.08, 1.8)], greenMat);
  } else if (phase === 2) {
    // EW Through & Right
    createCurvedRibbon(group, [new THREE.Vector3(18, 0.08, 5.4), new THREE.Vector3(-18, 0.08, 5.4)], greenMat);
    createCurvedRibbon(group, [new THREE.Vector3(-18, 0.08, -5.4), new THREE.Vector3(18, 0.08, -5.4)], greenMat);
  } else if (phase === 3) {
    // EW Left
    createCurvedRibbon(group, [new THREE.Vector3(18, 0.08, 1.8), new THREE.Vector3(4, 0.08, 1.8), new THREE.Vector3(1.8, 0.08, -8), new THREE.Vector3(1.8, 0.08, -18)], greenMat);
    createCurvedRibbon(group, [new THREE.Vector3(-18, 0.08, -1.8), new THREE.Vector3(-4, 0.08, -1.8), new THREE.Vector3(-1.8, 0.08, 8), new THREE.Vector3(-1.8, 0.08, 18)], greenMat);
  }
}

function createCurvedRibbon(parent: THREE.Group, points: THREE.Vector3[], material: THREE.Material) {
  const curve = new THREE.CatmullRomCurve3(points);
  const tubeGeo = new THREE.TubeGeometry(curve, 20, 0.35, 8, false);
  const mesh = new THREE.Mesh(tubeGeo, material);
  parent.add(mesh);
}

// Smooth Camera Transition according to active preset
function updateCameraInterpolation(
  camera: THREE.PerspectiveCamera,
  controls: OrbitControls,
  preset: CameraViewPreset,
  dt: number,
  vehicles: Vehicle[]
) {
  const dampFactor = Math.min(1.0, dt * 3.5);

  switch (preset) {
    case 'aerial':
      _camPos.set(0, 95, 42);
      _targetPos.set(0, 0, 0);
      break;
    case 'street':
      _camPos.set(14, 3.2, 28);
      _targetPos.set(0, 2.5, 0);
      break;
    case 'top_down':
      _camPos.set(0.01, 115, 0.01);
      _targetPos.set(0, 0, 0);
      break;
  }

  camera.position.lerp(_camPos, dampFactor);
  controls.target.lerp(_targetPos, dampFactor);
}

// Environmental atmospheric updates (Day / Night / Monsoon / Fog)
function updateEnvironment(
  weather: WeatherMode,
  scene: THREE.Scene,
  dirLight: THREE.DirectionalLight | null,
  hemiLight: THREE.HemisphereLight | null,
  rainSystem: THREE.Points | null,
  dt: number
) {
  if (weather === 'day') {
    scene.background = new THREE.Color(0x0a0f18);
    if (scene.fog) (scene.fog as THREE.FogExp2).density = 0.005;
    if (dirLight) dirLight.intensity = 2.4;
    if (hemiLight) hemiLight.intensity = 1.2;
    if (rainSystem) rainSystem.visible = false;
  } else if (weather === 'night') {
    scene.background = new THREE.Color(0x04070e);
    if (scene.fog) (scene.fog as THREE.FogExp2).density = 0.008;
    if (dirLight) dirLight.intensity = 0.45;
    if (hemiLight) hemiLight.intensity = 0.35;
    if (rainSystem) rainSystem.visible = false;
  } else if (weather === 'monsoon') {
    scene.background = new THREE.Color(0x08101a);
    if (scene.fog) (scene.fog as THREE.FogExp2).density = 0.014;
    if (dirLight) dirLight.intensity = 1.2;
    if (hemiLight) hemiLight.intensity = 0.8;
    if (rainSystem) {
      rainSystem.visible = true;
      const positions = rainSystem.geometry.attributes.position.array as Float32Array;
      for (let i = 1; i < positions.length; i += 3) {
        positions[i] -= dt * 65;
        if (positions[i] < 0) positions[i] = 60;
      }
      rainSystem.geometry.attributes.position.needsUpdate = true;
    }
  } else if (weather === 'fog') {
    scene.background = new THREE.Color(0x111c2e);
    if (scene.fog) (scene.fog as THREE.FogExp2).density = 0.022;
    if (dirLight) dirLight.intensity = 1.0;
    if (hemiLight) hemiLight.intensity = 0.9;
    if (rainSystem) rainSystem.visible = false;
  }
}

// Position & Rotation calculations for vehicle along entry -> intersection curve -> exit
function computeVehicleWorldPosition(v: Vehicle): { x: number; y: number; z: number; heading: number } {
  const totalLength = APPROACH_LENGTH * 2;
  const stopDist = APPROACH_LENGTH - INTERSECTION_RADIUS; // e.g. 92m
  const stopProgress = stopDist / totalLength; // 0.418
  const exitProgress = (APPROACH_LENGTH + INTERSECTION_RADIUS) / totalLength; // 0.582

  // Inbound lane offset from center line
  // lane 0: 1.8m, lane 1: 5.4m, lane 2: 9.0m
  const laneOffset = 1.8 + v.laneIndex * LANE_WIDTH;

  if (v.progress <= stopProgress) {
    // 1. Entry Approach Phase
    const dFromCenter = (stopProgress - v.progress) * totalLength + INTERSECTION_RADIUS;

    switch (v.approach) {
      case 'north':
        return { x: laneOffset, y: 0, z: -dFromCenter, heading: 0 };
      case 'south':
        return { x: -laneOffset, y: 0, z: dFromCenter, heading: Math.PI };
      case 'east':
        return { x: dFromCenter, y: 0, z: laneOffset, heading: Math.PI / 2 };
      case 'west':
        return { x: -dFromCenter, y: 0, z: -laneOffset, heading: -Math.PI / 2 };
    }
  } else if (v.progress < exitProgress) {
    // 2. Intersection Traversal Phase (straight or turning)
    const t = (v.progress - stopProgress) / (exitProgress - stopProgress); // 0 to 1

    if (v.movement === 'through') {
      const zInter = -INTERSECTION_RADIUS + t * (INTERSECTION_RADIUS * 2);
      switch (v.approach) {
        case 'north':
          return { x: laneOffset, y: 0, z: zInter, heading: 0 };
        case 'south':
          return { x: -laneOffset, y: 0, z: -zInter, heading: Math.PI };
        case 'east':
          return { x: -zInter, y: 0, z: laneOffset, heading: Math.PI / 2 };
        case 'west':
          return { x: zInter, y: 0, z: -laneOffset, heading: -Math.PI / 2 };
      }
    } else if (v.movement === 'left') {
      // 90 deg counter-clockwise turn
      const angle = t * (Math.PI / 2);
      const r = INTERSECTION_RADIUS * 0.85;

      switch (v.approach) {
        case 'north':
          return {
            x: laneOffset - (1 - Math.cos(angle)) * (laneOffset + r),
            y: 0,
            z: -INTERSECTION_RADIUS + Math.sin(angle) * r,
            heading: -angle,
          };
        case 'south':
          return {
            x: -laneOffset + (1 - Math.cos(angle)) * (laneOffset + r),
            y: 0,
            z: INTERSECTION_RADIUS - Math.sin(angle) * r,
            heading: Math.PI - angle,
          };
        case 'east':
          return {
            x: INTERSECTION_RADIUS - Math.sin(angle) * r,
            y: 0,
            z: laneOffset - (1 - Math.cos(angle)) * (laneOffset + r),
            heading: Math.PI / 2 - angle,
          };
        case 'west':
          return {
            x: -INTERSECTION_RADIUS + Math.sin(angle) * r,
            y: 0,
            z: -laneOffset + (1 - Math.cos(angle)) * (laneOffset + r),
            heading: -Math.PI / 2 - angle,
          };
      }
    } else {
      // Right turn (tight 90 deg clockwise turn)
      const angle = t * (Math.PI / 2);
      const r = 8.5;
      switch (v.approach) {
        case 'north':
          return {
            x: laneOffset + (1 - Math.cos(angle)) * r,
            y: 0,
            z: -INTERSECTION_RADIUS + Math.sin(angle) * r,
            heading: angle,
          };
        case 'south':
          return {
            x: -laneOffset - (1 - Math.cos(angle)) * r,
            y: 0,
            z: INTERSECTION_RADIUS - Math.sin(angle) * r,
            heading: Math.PI + angle,
          };
        case 'east':
          return {
            x: INTERSECTION_RADIUS - Math.sin(angle) * r,
            y: 0,
            z: laneOffset + (1 - Math.cos(angle)) * r,
            heading: Math.PI / 2 + angle,
          };
        case 'west':
          return {
            x: -INTERSECTION_RADIUS + Math.sin(angle) * r,
            y: 0,
            z: -laneOffset - (1 - Math.cos(angle)) * r,
            heading: -Math.PI / 2 + angle,
          };
      }
    }
  } else {
    // 3. Exit Outbound Departure Phase
    const dFromCenter = INTERSECTION_RADIUS + (v.progress - exitProgress) * totalLength;
    const outboundLaneOffset = 1.8 + v.laneIndex * LANE_WIDTH;

    switch (v.approach) {
      case 'north':
        return { x: outboundLaneOffset, y: 0, z: dFromCenter, heading: 0 };
      case 'south':
        return { x: -outboundLaneOffset, y: 0, z: -dFromCenter, heading: Math.PI };
      case 'east':
        return { x: -dFromCenter, y: 0, z: outboundLaneOffset, heading: Math.PI / 2 };
      case 'west':
        return { x: dFromCenter, y: 0, z: -outboundLaneOffset, heading: -Math.PI / 2 };
    }
  }
}

// Efficient Mesh Synchronization
function updateVehicles(
  scene: THREE.Scene,
  meshMap: Map<string, THREE.Group>,
  currentVehicles: Vehicle[],
  dt: number
) {
  const currentIds = new Set(currentVehicles.map((v) => v.id));

  // 1. Remove meshes for departed vehicles
  meshMap.forEach((mesh, id) => {
    if (!currentIds.has(id)) {
      scene.remove(mesh);
      meshMap.delete(id);
    }
  });

  // 2. Add or update active vehicle meshes
  currentVehicles.forEach((v) => {
    let group = meshMap.get(v.id);
    if (!group) {
      group = buildProceduralVehicle(v.type, v.color);
      scene.add(group);
      meshMap.set(v.id, group);
    }

    const { x, y, z, heading } = computeVehicleWorldPosition(v);
    group.position.set(x, y, z);
    group.rotation.y = heading;

    // Siren flashing animation for emergency vehicle
    if (v.isEmergency) {
      const isRed = Math.floor(performance.now() / 150) % 2 === 0;
      group.children.forEach((c) => {
        if (c instanceof THREE.Mesh && (c.material as THREE.MeshStandardMaterial).emissive) {
          const mat = c.material as THREE.MeshStandardMaterial;
          if (mat.color.getHex() === 0xff0000) {
            mat.emissiveIntensity = isRed ? 4.5 : 0.2;
          } else if (mat.color.getHex() === 0x0088ff) {
            mat.emissiveIntensity = !isRed ? 4.5 : 0.2;
          }
        }
      });
    }
  });
}
