/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import * as THREE from 'three';
import {
  createAsphaltTexture,
  createBuildingWindowTexture,
  createSidewalkTexture,
} from './materials.ts';
import { SignalLightColor } from '../../types/traffic.ts';

export interface TrafficSignalMeshGroup {
  poleGroup: THREE.Group;
  direction: 'north' | 'south' | 'east' | 'west';
  throughRed: THREE.Mesh;
  throughYellow: THREE.Mesh;
  throughGreen: THREE.Mesh;
  leftRed: THREE.Mesh;
  leftYellow: THREE.Mesh;
  leftGreen: THREE.Mesh;
}

export function buildIntersectionScene(): {
  cityGroup: THREE.Group;
  signals: Record<'north' | 'south' | 'east' | 'west', TrafficSignalMeshGroup>;
} {
  const cityGroup = new THREE.Group();

  const asphaltTex = createAsphaltTexture();
  const sidewalkTex = createSidewalkTexture();
  const windowTex = createBuildingWindowTexture(0.7);

  // 1. Ground base
  const groundGeo = new THREE.PlaneGeometry(320, 320);
  const groundMat = new THREE.MeshStandardMaterial({
    color: 0x0a0f18,
    roughness: 0.95,
  });
  const ground = new THREE.Mesh(groundGeo, groundMat);
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -0.05;
  ground.receiveShadow = true;
  cityGroup.add(ground);

  // 2. Asphalt Road Surface
  const roadMat = new THREE.MeshStandardMaterial({
    map: asphaltTex,
    color: 0x222a36,
    roughness: 0.8,
    metalness: 0.1,
  });

  const ROAD_WIDTH = 22.4; // 6 lanes total (3 inbound, 3 outbound)
  const ROAD_LEN = 260;

  // NS Road
  const nsRoad = new THREE.Mesh(new THREE.PlaneGeometry(ROAD_WIDTH, ROAD_LEN), roadMat);
  nsRoad.rotation.x = -Math.PI / 2;
  nsRoad.position.y = 0.01;
  nsRoad.receiveShadow = true;
  cityGroup.add(nsRoad);

  // EW Road
  const ewRoad = new THREE.Mesh(new THREE.PlaneGeometry(ROAD_LEN, ROAD_WIDTH), roadMat);
  ewRoad.rotation.x = -Math.PI / 2;
  ewRoad.position.y = 0.012;
  ewRoad.receiveShadow = true;
  cityGroup.add(ewRoad);

  // 3. Road Markings Material (polygonOffset to prevent z-fighting)
  const whiteMarkingMat = new THREE.MeshBasicMaterial({
    color: 0xedf2f7,
    polygonOffset: true,
    polygonOffsetFactor: -1,
    polygonOffsetUnits: -1,
  });

  const yellowMarkingMat = new THREE.MeshBasicMaterial({
    color: 0xfacc15,
    polygonOffset: true,
    polygonOffsetFactor: -1,
    polygonOffsetUnits: -1,
  });

  // A. Double Yellow Centerlines (separating oncoming traffic)
  const doubleYellowGeo = new THREE.PlaneGeometry(0.18, 100);

  // North Approach Centerline
  const clNorth1 = new THREE.Mesh(doubleYellowGeo, yellowMarkingMat);
  clNorth1.rotation.x = -Math.PI / 2;
  clNorth1.position.set(-0.16, 0.02, -70);
  const clNorth2 = new THREE.Mesh(doubleYellowGeo, yellowMarkingMat);
  clNorth2.rotation.x = -Math.PI / 2;
  clNorth2.position.set(0.16, 0.02, -70);

  // South Approach Centerline
  const clSouth1 = new THREE.Mesh(doubleYellowGeo, yellowMarkingMat);
  clSouth1.rotation.x = -Math.PI / 2;
  clSouth1.position.set(-0.16, 0.02, 70);
  const clSouth2 = new THREE.Mesh(doubleYellowGeo, yellowMarkingMat);
  clSouth2.rotation.x = -Math.PI / 2;
  clSouth2.position.set(0.16, 0.02, 70);

  // East Approach Centerline
  const doubleYellowGeoH = new THREE.PlaneGeometry(100, 0.18);
  const clEast1 = new THREE.Mesh(doubleYellowGeoH, yellowMarkingMat);
  clEast1.rotation.x = -Math.PI / 2;
  clEast1.position.set(70, 0.02, -0.16);
  const clEast2 = new THREE.Mesh(doubleYellowGeoH, yellowMarkingMat);
  clEast2.rotation.x = -Math.PI / 2;
  clEast2.position.set(70, 0.02, 0.16);

  // West Approach Centerline
  const clWest1 = new THREE.Mesh(doubleYellowGeoH, yellowMarkingMat);
  clWest1.rotation.x = -Math.PI / 2;
  clWest1.position.set(-70, 0.02, -0.16);
  const clWest2 = new THREE.Mesh(doubleYellowGeoH, yellowMarkingMat);
  clWest2.rotation.x = -Math.PI / 2;
  clWest2.position.set(-70, 0.02, 0.16);

  cityGroup.add(clNorth1, clNorth2, clSouth1, clSouth2, clEast1, clEast2, clWest1, clWest2);

  // B. Dashed White Lane Dividers
  const dashGeo = new THREE.PlaneGeometry(0.16, 2.5);
  for (let z = 22; z < 120; z += 5) {
    // North inbound lanes (x > 0 for right hand traffic, so inbound is on one side)
    // Inbound: lane 0 (x = 1.8), lane 1 (x = 5.4), lane 2 (x = 9.0)
    [-3.6, -7.2, 3.6, 7.2].forEach((xOff) => {
      const dashN = new THREE.Mesh(dashGeo, whiteMarkingMat);
      dashN.rotation.x = -Math.PI / 2;
      dashN.position.set(xOff, 0.02, -z);

      const dashS = new THREE.Mesh(dashGeo, whiteMarkingMat);
      dashS.rotation.x = -Math.PI / 2;
      dashS.position.set(xOff, 0.02, z);

      cityGroup.add(dashN, dashS);
    });
  }

  const dashGeoH = new THREE.PlaneGeometry(2.5, 0.16);
  for (let x = 22; x < 120; x += 5) {
    [-3.6, -7.2, 3.6, 7.2].forEach((zOff) => {
      const dashE = new THREE.Mesh(dashGeoH, whiteMarkingMat);
      dashE.rotation.x = -Math.PI / 2;
      dashE.position.set(x, 0.02, zOff);

      const dashW = new THREE.Mesh(dashGeoH, whiteMarkingMat);
      dashW.rotation.x = -Math.PI / 2;
      dashW.position.set(-x, 0.02, zOff);

      cityGroup.add(dashE, dashW);
    });
  }

  // C. Stop Bars (Solid transverse lines 18m from center)
  const stopBarGeoV = new THREE.PlaneGeometry(10.8, 0.65);
  const stopBarGeoH = new THREE.PlaneGeometry(0.65, 10.8);

  const stopN = new THREE.Mesh(stopBarGeoV, whiteMarkingMat);
  stopN.rotation.x = -Math.PI / 2;
  stopN.position.set(5.5, 0.022, -18);

  const stopS = new THREE.Mesh(stopBarGeoV, whiteMarkingMat);
  stopS.rotation.x = -Math.PI / 2;
  stopS.position.set(-5.5, 0.022, 18);

  const stopE = new THREE.Mesh(stopBarGeoH, whiteMarkingMat);
  stopE.rotation.x = -Math.PI / 2;
  stopE.position.set(18, 0.022, 5.5);

  const stopW = new THREE.Mesh(stopBarGeoH, whiteMarkingMat);
  stopW.rotation.x = -Math.PI / 2;
  stopW.position.set(-18, 0.022, -5.5);

  cityGroup.add(stopN, stopS, stopE, stopW);

  // D. Zebra Crosswalks (Pedestrian crossings right behind stop bars)
  const stripeGeoV = new THREE.PlaneGeometry(0.55, 3.8);
  const stripeGeoH = new THREE.PlaneGeometry(3.8, 0.55);

  for (let s = -10.5; s <= 10.5; s += 1.2) {
    // North crosswalk
    const zwN = new THREE.Mesh(stripeGeoV, whiteMarkingMat);
    zwN.rotation.x = -Math.PI / 2;
    zwN.position.set(s, 0.022, -14.2);

    // South crosswalk
    const zwS = new THREE.Mesh(stripeGeoV, whiteMarkingMat);
    zwS.rotation.x = -Math.PI / 2;
    zwS.position.set(s, 0.022, 14.2);

    // East crosswalk
    const zwE = new THREE.Mesh(stripeGeoH, whiteMarkingMat);
    zwE.rotation.x = -Math.PI / 2;
    zwE.position.set(14.2, 0.022, s);

    // West crosswalk
    const zwW = new THREE.Mesh(stripeGeoH, whiteMarkingMat);
    zwW.rotation.x = -Math.PI / 2;
    zwW.position.set(-14.2, 0.022, s);

    cityGroup.add(zwN, zwS, zwE, zwW);
  }

  // 4. Sidewalks & Curbs
  const sidewalkMat = new THREE.MeshStandardMaterial({
    map: sidewalkTex,
    color: 0x334155,
    roughness: 0.9,
  });

  const curbMat = new THREE.MeshStandardMaterial({
    color: 0x64748b,
    roughness: 0.7,
  });

  const CORNER_OFFSET = 11.2;
  const BLOCK_SIZE = 120;

  // 4 Quadrants of Sidewalks
  const corners = [
    { x: CORNER_OFFSET + BLOCK_SIZE / 2, z: -(CORNER_OFFSET + BLOCK_SIZE / 2) }, // NE
    { x: -(CORNER_OFFSET + BLOCK_SIZE / 2), z: -(CORNER_OFFSET + BLOCK_SIZE / 2) }, // NW
    { x: CORNER_OFFSET + BLOCK_SIZE / 2, z: CORNER_OFFSET + BLOCK_SIZE / 2 }, // SE
    { x: -(CORNER_OFFSET + BLOCK_SIZE / 2), z: CORNER_OFFSET + BLOCK_SIZE / 2 }, // SW
  ];

  corners.forEach((c) => {
    const sw = new THREE.Mesh(new THREE.BoxGeometry(BLOCK_SIZE, 0.32, BLOCK_SIZE), sidewalkMat);
    sw.position.set(c.x, 0.16, c.z);
    sw.receiveShadow = true;
    cityGroup.add(sw);
  });

  // 5. Buildings / Commercial Skyline
  const buildingMat = new THREE.MeshStandardMaterial({
    map: windowTex,
    color: 0x1e293b,
    roughness: 0.45,
    metalness: 0.35,
  });

  const buildingSpecs = [
    // NE Quadrant
    { x: 32, z: -32, w: 28, d: 28, h: 58 },
    { x: 68, z: -34, w: 32, d: 26, h: 74 },
    { x: 34, z: -70, w: 26, d: 34, h: 46 },
    { x: 72, z: -72, w: 34, d: 34, h: 86 },

    // NW Quadrant
    { x: -32, z: -32, w: 28, d: 28, h: 64 },
    { x: -68, z: -34, w: 32, d: 26, h: 52 },
    { x: -34, z: -70, w: 26, d: 34, h: 78 },
    { x: -72, z: -72, w: 34, d: 34, h: 48 },

    // SE Quadrant
    { x: 32, z: 32, w: 28, d: 28, h: 50 },
    { x: 68, z: 34, w: 32, d: 26, h: 68 },
    { x: 34, z: 70, w: 26, d: 34, h: 82 },
    { x: 72, z: 72, w: 34, d: 34, h: 60 },

    // SW Quadrant
    { x: -32, z: 32, w: 28, d: 28, h: 72 },
    { x: -68, z: 34, w: 32, d: 26, h: 55 },
    { x: -34, z: 70, w: 26, d: 34, h: 42 },
    { x: -72, z: 72, w: 34, d: 34, h: 90 },
  ];

  buildingSpecs.forEach((b) => {
    const bMesh = new THREE.Mesh(new THREE.BoxGeometry(b.w, b.h, b.d), buildingMat);
    bMesh.position.set(b.x, b.h / 2 + 0.32, b.z);
    bMesh.castShadow = true;
    bMesh.receiveShadow = true;
    cityGroup.add(bMesh);

    // Roof equipment / chillers
    const roofEquip = new THREE.Mesh(
      new THREE.BoxGeometry(b.w * 0.45, 2.2, b.d * 0.45),
      new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.8 })
    );
    roofEquip.position.set(b.x, b.h + 1.4, b.z);
    cityGroup.add(roofEquip);
  });

  // 6. Street Furniture: Street Trees & Streetlights
  const trunkGeo = new THREE.CylinderGeometry(0.2, 0.25, 3.5, 8);
  const trunkMat = new THREE.MeshStandardMaterial({ color: 0x3d271d, roughness: 0.9 });
  const foliageGeo = new THREE.SphereGeometry(1.6, 8, 8);
  const foliageMat = new THREE.MeshStandardMaterial({ color: 0x166534, roughness: 0.7 });

  const treePositions = [
    { x: 13.5, z: -25 }, { x: 13.5, z: -45 }, { x: 13.5, z: -65 },
    { x: -13.5, z: -25 }, { x: -13.5, z: -45 }, { x: -13.5, z: -65 },
    { x: 13.5, z: 25 }, { x: 13.5, z: 45 }, { x: 13.5, z: 65 },
    { x: -13.5, z: 25 }, { x: -13.5, z: 45 }, { x: -13.5, z: 65 },
    { x: 25, z: 13.5 }, { x: 45, z: 13.5 }, { x: 65, z: 13.5 },
    { x: -25, z: 13.5 }, { x: -45, z: 13.5 }, { x: -65, z: 13.5 },
  ];

  treePositions.forEach((tp) => {
    const treeGroup = new THREE.Group();
    treeGroup.position.set(tp.x, 0.32, tp.z);

    const trunk = new THREE.Mesh(trunkGeo, trunkMat);
    trunk.position.y = 1.75;
    trunk.castShadow = true;

    const foliage = new THREE.Mesh(foliageGeo, foliageMat);
    foliage.position.y = 4.2;
    foliage.castShadow = true;

    treeGroup.add(trunk, foliage);
    cityGroup.add(treeGroup);
  });

  // 7. Traffic Signal Mast Arm Poles with 3-Aspect Signal Heads
  const signals: Record<'north' | 'south' | 'east' | 'west', TrafficSignalMeshGroup> = {
    north: createSignalGantry('north', 12.2, -17.5, Math.PI),
    south: createSignalGantry('south', -12.2, 17.5, 0),
    east: createSignalGantry('east', 17.5, 12.2, -Math.PI / 2),
    west: createSignalGantry('west', -17.5, -12.2, Math.PI / 2),
  };

  Object.values(signals).forEach((s) => cityGroup.add(s.poleGroup));

  return { cityGroup, signals };
}

function createSignalGantry(
  direction: 'north' | 'south' | 'east' | 'west',
  x: number,
  z: number,
  rotationY: number
): TrafficSignalMeshGroup {
  const poleGroup = new THREE.Group();
  poleGroup.position.set(x, 0.32, z);
  poleGroup.rotation.y = rotationY;

  const steelMat = new THREE.MeshStandardMaterial({
    color: 0x374151,
    metalness: 0.85,
    roughness: 0.25,
  });

  // Vertical post (height 6.5m)
  const post = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.24, 6.5, 12), steelMat);
  post.position.y = 3.25;
  post.castShadow = true;
  poleGroup.add(post);

  // Horizontal cantilever mast arm (extends 8m over roadway)
  const arm = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.16, 8.2, 12), steelMat);
  arm.rotation.z = Math.PI / 2;
  arm.position.set(-4.1, 6.2, 0);
  poleGroup.add(arm);

  // Through & Right Signal Head (over middle lane)
  const headThrough = create3AspectSignalHead();
  headThrough.headGroup.position.set(-5.5, 5.4, 0);
  poleGroup.add(headThrough.headGroup);

  // Protected Left Signal Head (over left lane)
  const headLeft = create3AspectSignalHead(true);
  headLeft.headGroup.position.set(-2.4, 5.4, 0);
  poleGroup.add(headLeft.headGroup);

  return {
    poleGroup,
    direction,
    throughRed: headThrough.redLens,
    throughYellow: headThrough.yellowLens,
    throughGreen: headThrough.greenLens,
    leftRed: headLeft.redLens,
    leftYellow: headLeft.yellowLens,
    leftGreen: headLeft.greenLens,
  };
}

function create3AspectSignalHead(isLeftTurn: boolean = false) {
  const headGroup = new THREE.Group();

  // Black housing
  const housingMat = new THREE.MeshStandardMaterial({ color: 0x111827, roughness: 0.7 });
  const housing = new THREE.Mesh(new THREE.BoxGeometry(0.48, 1.35, 0.32), housingMat);
  housing.position.y = 0;
  headGroup.add(housing);

  // Backplate / Visor
  const backplateMat = new THREE.MeshStandardMaterial({ color: 0x030712 });
  const backplate = new THREE.Mesh(new THREE.BoxGeometry(0.68, 1.55, 0.04), backplateMat);
  backplate.position.set(0, 0, -0.16);
  headGroup.add(backplate);

  // 3 Lenses
  const lensGeo = new THREE.CylinderGeometry(0.14, 0.14, 0.08, 16);

  // Red
  const redMat = new THREE.MeshStandardMaterial({
    color: 0x330000,
    emissive: 0xff0000,
    emissiveIntensity: 0.2,
    roughness: 0.2,
  });
  const redLens = new THREE.Mesh(lensGeo, redMat);
  redLens.rotation.x = Math.PI / 2;
  redLens.position.set(0, 0.42, 0.15);

  // Yellow
  const yellowMat = new THREE.MeshStandardMaterial({
    color: 0x332200,
    emissive: 0xfbbf24,
    emissiveIntensity: 0.2,
    roughness: 0.2,
  });
  const yellowLens = new THREE.Mesh(lensGeo, yellowMat);
  yellowLens.rotation.x = Math.PI / 2;
  yellowLens.position.set(0, 0, 0.15);

  // Green
  const greenMat = new THREE.MeshStandardMaterial({
    color: 0x003311,
    emissive: 0x10b981,
    emissiveIntensity: 0.2,
    roughness: 0.2,
  });
  const greenLens = new THREE.Mesh(lensGeo, greenMat);
  greenLens.rotation.x = Math.PI / 2;
  greenLens.position.set(0, -0.42, 0.15);

  headGroup.add(redLens, yellowLens, greenLens);

  return {
    headGroup,
    redLens,
    yellowLens,
    greenLens,
  };
}

export function updateSignalLensColors(
  signalGroup: TrafficSignalMeshGroup,
  throughState: SignalLightColor,
  leftState: SignalLightColor
) {
  // Update Through
  setLensState(signalGroup.throughRed, throughState === 'red', 0xff0000, 2.8);
  setLensState(signalGroup.throughYellow, throughState === 'yellow', 0xf59e0b, 2.5);
  setLensState(signalGroup.throughGreen, throughState === 'green', 0x10b981, 2.8);

  // Update Left
  setLensState(signalGroup.leftRed, leftState === 'red', 0xff0000, 2.8);
  setLensState(signalGroup.leftYellow, leftState === 'yellow', 0xf59e0b, 2.5);
  setLensState(signalGroup.leftGreen, leftState === 'green', 0x10b981, 2.8);
}

function setLensState(lensMesh: THREE.Mesh, isActive: boolean, emissiveHex: number, activeIntensity: number) {
  const mat = lensMesh.material as THREE.MeshStandardMaterial;
  if (isActive) {
    mat.emissive.setHex(emissiveHex);
    mat.emissiveIntensity = activeIntensity;
  } else {
    mat.emissive.setHex(0x111111);
    mat.emissiveIntensity = 0.05;
  }
}
