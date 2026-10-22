/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import * as THREE from 'three';
import { VehicleType } from '../../types/traffic.ts';

// Shared geometries and materials cached to optimize draw calls and memory
const wheelGeo = new THREE.CylinderGeometry(0.36, 0.36, 0.24, 16);
const rimGeo = new THREE.CylinderGeometry(0.22, 0.22, 0.25, 12);
const tireMat = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.9, metalness: 0.1 });
const rimMat = new THREE.MeshStandardMaterial({ color: 0xdcdde1, roughness: 0.3, metalness: 0.85 });

const glassMat = new THREE.MeshPhysicalMaterial({
  color: 0x1e272e,
  roughness: 0.1,
  metalness: 0.2,
  transparent: true,
  opacity: 0.85,
});

const headlightMat = new THREE.MeshStandardMaterial({
  color: 0xffffff,
  emissive: 0xfffae6,
  emissiveIntensity: 1.5,
  roughness: 0.1,
});

const taillightMat = new THREE.MeshStandardMaterial({
  color: 0xff3838,
  emissive: 0xff2222,
  emissiveIntensity: 1.8,
  roughness: 0.1,
});

const sirenRedMat = new THREE.MeshStandardMaterial({
  color: 0xff0000,
  emissive: 0xff0033,
  emissiveIntensity: 3.0,
  roughness: 0.2,
});

const sirenBlueMat = new THREE.MeshStandardMaterial({
  color: 0x0088ff,
  emissive: 0x00a8ff,
  emissiveIntensity: 3.0,
  roughness: 0.2,
});

function createWheelMesh(x: number, y: number, z: number): THREE.Group {
  const wheelGroup = new THREE.Group();
  wheelGroup.position.set(x, y, z);
  wheelGroup.rotation.z = Math.PI / 2;

  const tire = new THREE.Mesh(wheelGeo, tireMat);
  tire.castShadow = true;
  wheelGroup.add(tire);

  const rim = new THREE.Mesh(rimGeo, rimMat);
  wheelGroup.add(rim);

  return wheelGroup;
}

export function buildProceduralVehicle(type: VehicleType, hexColor: string): THREE.Group {
  const vehicleGroup = new THREE.Group();
  const bodyColor = new THREE.Color(hexColor);
  const paintMat = new THREE.MeshStandardMaterial({
    color: bodyColor,
    roughness: 0.3,
    metalness: 0.65,
  });

  switch (type) {
    case 'car': {
      // 1. Lower chassis
      const chassisGeo = new THREE.BoxGeometry(1.85, 0.55, 4.4);
      const chassis = new THREE.Mesh(chassisGeo, paintMat);
      chassis.position.y = 0.55;
      chassis.castShadow = true;
      chassis.receiveShadow = true;
      vehicleGroup.add(chassis);

      // 2. Cabin / Greenhouse
      const cabinGeo = new THREE.BoxGeometry(1.5, 0.52, 2.3);
      const cabin = new THREE.Mesh(cabinGeo, glassMat);
      cabin.position.set(0, 1.05, -0.2);
      cabin.castShadow = true;
      vehicleGroup.add(cabin);

      // 3. Roof panel
      const roofGeo = new THREE.BoxGeometry(1.46, 0.06, 2.1);
      const roof = new THREE.Mesh(roofGeo, paintMat);
      roof.position.set(0, 1.33, -0.2);
      vehicleGroup.add(roof);

      // 4-7. Wheels
      vehicleGroup.add(createWheelMesh(-0.95, 0.36, 1.3));
      vehicleGroup.add(createWheelMesh(0.95, 0.36, 1.3));
      vehicleGroup.add(createWheelMesh(-0.95, 0.36, -1.3));
      vehicleGroup.add(createWheelMesh(0.95, 0.36, -1.3));

      // 8-9. Headlights
      const hlGeo = new THREE.BoxGeometry(0.32, 0.14, 0.08);
      const hlL = new THREE.Mesh(hlGeo, headlightMat);
      hlL.position.set(-0.65, 0.6, 2.22);
      const hlR = new THREE.Mesh(hlGeo, headlightMat);
      hlR.position.set(0.65, 0.6, 2.22);
      vehicleGroup.add(hlL, hlR);

      // 10-11. Taillights
      const tlGeo = new THREE.BoxGeometry(0.34, 0.12, 0.08);
      const tlL = new THREE.Mesh(tlGeo, taillightMat);
      tlL.position.set(-0.65, 0.62, -2.22);
      const tlR = new THREE.Mesh(tlGeo, taillightMat);
      tlR.position.set(0.65, 0.62, -2.22);
      vehicleGroup.add(tlL, tlR);
      break;
    }

    case 'suv': {
      // 1. Bulkier chassis
      const chassisGeo = new THREE.BoxGeometry(2.0, 0.72, 4.8);
      const chassis = new THREE.Mesh(chassisGeo, paintMat);
      chassis.position.y = 0.68;
      chassis.castShadow = true;
      chassis.receiveShadow = true;
      vehicleGroup.add(chassis);

      // 2. High cabin
      const cabinGeo = new THREE.BoxGeometry(1.7, 0.65, 3.1);
      const cabin = new THREE.Mesh(cabinGeo, glassMat);
      cabin.position.set(0, 1.3, -0.4);
      cabin.castShadow = true;
      vehicleGroup.add(cabin);

      // 3. Roof rack bars
      const rackGeo = new THREE.BoxGeometry(1.5, 0.08, 2.8);
      const rackMat = new THREE.MeshStandardMaterial({ color: 0x222222, metalness: 0.9, roughness: 0.2 });
      const rack = new THREE.Mesh(rackGeo, rackMat);
      rack.position.set(0, 1.66, -0.4);
      vehicleGroup.add(rack);

      // 4-7. Wheels
      vehicleGroup.add(createWheelMesh(-1.02, 0.42, 1.45));
      vehicleGroup.add(createWheelMesh(1.02, 0.42, 1.45));
      vehicleGroup.add(createWheelMesh(-1.02, 0.42, -1.45));
      vehicleGroup.add(createWheelMesh(1.02, 0.42, -1.45));

      // Headlights & taillights
      const hlL = new THREE.Mesh(new THREE.BoxGeometry(0.38, 0.18, 0.08), headlightMat);
      hlL.position.set(-0.72, 0.75, 2.42);
      const hlR = new THREE.Mesh(new THREE.BoxGeometry(0.38, 0.18, 0.08), headlightMat);
      hlR.position.set(0.72, 0.75, 2.42);
      const tlL = new THREE.Mesh(new THREE.BoxGeometry(0.38, 0.18, 0.08), taillightMat);
      tlL.position.set(-0.72, 0.75, -2.42);
      const tlR = new THREE.Mesh(new THREE.BoxGeometry(0.38, 0.18, 0.08), taillightMat);
      tlR.position.set(0.72, 0.75, -2.42);
      vehicleGroup.add(hlL, hlR, tlL, tlR);
      break;
    }

    case 'bus': {
      // 1. Long transit bus body
      const busBodyGeo = new THREE.BoxGeometry(2.5, 2.2, 11.2);
      const busMat = new THREE.MeshStandardMaterial({ color: bodyColor, roughness: 0.35, metalness: 0.4 });
      const body = new THREE.Mesh(busBodyGeo, busMat);
      body.position.y = 1.45;
      body.castShadow = true;
      body.receiveShadow = true;
      vehicleGroup.add(body);

      // 2. Side window strips
      const windowStripGeo = new THREE.BoxGeometry(2.54, 0.75, 9.6);
      const windowStrip = new THREE.Mesh(windowStripGeo, glassMat);
      windowStrip.position.set(0, 1.8, -0.2);
      vehicleGroup.add(windowStrip);

      // 3. Front Windshield & Route display
      const destSignGeo = new THREE.BoxGeometry(1.6, 0.28, 0.1);
      const destSignMat = new THREE.MeshStandardMaterial({ color: 0x000000, emissive: 0xffaa00, emissiveIntensity: 1.2 });
      const destSign = new THREE.Mesh(destSignGeo, destSignMat);
      destSign.position.set(0, 2.3, 5.62);
      vehicleGroup.add(destSign);

      // 4. Roof AC Units
      const acUnitGeo = new THREE.BoxGeometry(1.6, 0.28, 2.4);
      const acUnitMat = new THREE.MeshStandardMaterial({ color: 0xdddddd, roughness: 0.5 });
      const acUnit = new THREE.Mesh(acUnitGeo, acUnitMat);
      acUnit.position.set(0, 2.68, 0);
      vehicleGroup.add(acUnit);

      // 5-10. 6 Wheels
      vehicleGroup.add(createWheelMesh(-1.26, 0.45, 3.8));
      vehicleGroup.add(createWheelMesh(1.26, 0.45, 3.8));
      vehicleGroup.add(createWheelMesh(-1.26, 0.45, -2.6));
      vehicleGroup.add(createWheelMesh(1.26, 0.45, -2.6));
      vehicleGroup.add(createWheelMesh(-1.26, 0.45, -3.9));
      vehicleGroup.add(createWheelMesh(1.26, 0.45, -3.9));

      // Headlights & Taillights
      const hlL = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.2, 0.1), headlightMat);
      hlL.position.set(-0.85, 0.7, 5.62);
      const hlR = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.2, 0.1), headlightMat);
      hlR.position.set(0.85, 0.7, 5.62);
      const tlL = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.2, 0.1), taillightMat);
      tlL.position.set(-0.85, 0.7, -5.62);
      const tlR = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.2, 0.1), taillightMat);
      tlR.position.set(0.85, 0.7, -5.62);
      vehicleGroup.add(hlL, hlR, tlL, tlR);
      break;
    }

    case 'truck': {
      // 1. Cab
      const cabGeo = new THREE.BoxGeometry(2.4, 1.8, 2.6);
      const cab = new THREE.Mesh(cabGeo, paintMat);
      cab.position.set(0, 1.25, 2.8);
      cab.castShadow = true;
      vehicleGroup.add(cab);

      // 2. Windshield
      const wsGeo = new THREE.BoxGeometry(2.1, 0.75, 0.6);
      const ws = new THREE.Mesh(wsGeo, glassMat);
      ws.position.set(0, 1.6, 3.8);
      vehicleGroup.add(ws);

      // 3. Cargo container box
      const containerGeo = new THREE.BoxGeometry(2.45, 2.2, 5.8);
      const containerMat = new THREE.MeshStandardMaterial({ color: 0x475569, roughness: 0.7, metalness: 0.3 });
      const container = new THREE.Mesh(containerGeo, containerMat);
      container.position.set(0, 1.5, -1.5);
      container.castShadow = true;
      vehicleGroup.add(container);

      // 4-9. Wheels
      vehicleGroup.add(createWheelMesh(-1.22, 0.45, 2.8));
      vehicleGroup.add(createWheelMesh(1.22, 0.45, 2.8));
      vehicleGroup.add(createWheelMesh(-1.22, 0.45, -2.2));
      vehicleGroup.add(createWheelMesh(1.22, 0.45, -2.2));
      vehicleGroup.add(createWheelMesh(-1.22, 0.45, -3.5));
      vehicleGroup.add(createWheelMesh(1.22, 0.45, -3.5));

      // Headlights
      const hlL = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.18, 0.08), headlightMat);
      hlL.position.set(-0.85, 0.65, 4.12);
      const hlR = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.18, 0.08), headlightMat);
      hlR.position.set(0.85, 0.65, 4.12);
      vehicleGroup.add(hlL, hlR);
      break;
    }

    case 'rickshaw': {
      // Auto-rickshaw 3-wheeler
      // 1. Lower body (green/yellow)
      const lowerGeo = new THREE.BoxGeometry(1.3, 0.55, 2.6);
      const lowerMat = new THREE.MeshStandardMaterial({ color: 0x16a34a, roughness: 0.4, metalness: 0.3 });
      const lower = new THREE.Mesh(lowerGeo, lowerMat);
      lower.position.y = 0.55;
      lower.castShadow = true;
      vehicleGroup.add(lower);

      // 2. Yellow Canvas Roof
      const roofGeo = new THREE.BoxGeometry(1.28, 0.8, 1.9);
      const yellowRoofMat = new THREE.MeshStandardMaterial({ color: 0xfacc15, roughness: 0.6, metalness: 0.1 });
      const canopy = new THREE.Mesh(roofGeo, yellowRoofMat);
      canopy.position.set(0, 1.15, -0.25);
      canopy.castShadow = true;
      vehicleGroup.add(canopy);

      // 3. Front Windscreen
      const rwsGeo = new THREE.BoxGeometry(1.0, 0.45, 0.06);
      const rws = new THREE.Mesh(rwsGeo, glassMat);
      rws.position.set(0, 1.05, 0.85);
      vehicleGroup.add(rws);

      // 4-6. 3 Wheels (1 front center, 2 rear)
      vehicleGroup.add(createWheelMesh(0, 0.3, 0.95));
      vehicleGroup.add(createWheelMesh(-0.68, 0.3, -0.85));
      vehicleGroup.add(createWheelMesh(0.68, 0.3, -0.85));

      // Central round headlight
      const hl = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 0.08, 12), headlightMat);
      hl.rotation.x = Math.PI / 2;
      hl.position.set(0, 0.65, 1.32);
      vehicleGroup.add(hl);
      break;
    }

    case 'motorcycle': {
      // Slender bike chassis
      const frameGeo = new THREE.BoxGeometry(0.35, 0.5, 2.1);
      const frameMat = new THREE.MeshStandardMaterial({ color: bodyColor, roughness: 0.3, metalness: 0.7 });
      const frame = new THREE.Mesh(frameGeo, frameMat);
      frame.position.y = 0.55;
      vehicleGroup.add(frame);

      // Handlebars
      const barGeo = new THREE.BoxGeometry(0.8, 0.06, 0.06);
      const barMat = new THREE.MeshStandardMaterial({ color: 0x111111, metalness: 0.9 });
      const bar = new THREE.Mesh(barGeo, barMat);
      bar.position.set(0, 0.95, 0.55);
      vehicleGroup.add(bar);

      // 2 wheels
      const fWheel = createWheelMesh(0, 0.32, 0.85);
      const rWheel = createWheelMesh(0, 0.32, -0.85);
      vehicleGroup.add(fWheel, rWheel);

      // Headlight
      const hl = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 0.08, 12), headlightMat);
      hl.rotation.x = Math.PI / 2;
      hl.position.set(0, 0.8, 1.06);
      vehicleGroup.add(hl);
      break;
    }

    case 'ambulance': {
      // White emergency medical van
      const bodyGeo = new THREE.BoxGeometry(2.2, 1.6, 5.6);
      const ambMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2, metalness: 0.5 });
      const ambBody = new THREE.Mesh(bodyGeo, ambMat);
      ambBody.position.y = 1.15;
      ambBody.castShadow = true;
      ambBody.receiveShadow = true;
      vehicleGroup.add(ambBody);

      // Red Stripe Decal
      const stripeGeo = new THREE.BoxGeometry(2.22, 0.3, 5.2);
      const redStripeMat = new THREE.MeshStandardMaterial({ color: 0xdc2626, roughness: 0.3 });
      const stripe = new THREE.Mesh(stripeGeo, redStripeMat);
      stripe.position.set(0, 1.15, 0);
      vehicleGroup.add(stripe);

      // Windshield
      const wsGeo = new THREE.BoxGeometry(1.9, 0.6, 0.5);
      const ws = new THREE.Mesh(wsGeo, glassMat);
      ws.position.set(0, 1.45, 2.3);
      vehicleGroup.add(ws);

      // Emergency Lightbar on roof (Dual Red & Blue strobe)
      const barBaseGeo = new THREE.BoxGeometry(1.4, 0.1, 0.3);
      const barBase = new THREE.Mesh(barBaseGeo, new THREE.MeshStandardMaterial({ color: 0x222222 }));
      barBase.position.set(0, 2.0, 1.2);
      vehicleGroup.add(barBase);

      const redStrobe = new THREE.Mesh(new THREE.BoxGeometry(0.55, 0.18, 0.25), sirenRedMat);
      redStrobe.position.set(-0.35, 2.12, 1.2);
      const blueStrobe = new THREE.Mesh(new THREE.BoxGeometry(0.55, 0.18, 0.25), sirenBlueMat);
      blueStrobe.position.set(0.35, 2.12, 1.2);
      vehicleGroup.add(redStrobe, blueStrobe);

      // Wheels
      vehicleGroup.add(createWheelMesh(-1.12, 0.4, 1.7));
      vehicleGroup.add(createWheelMesh(1.12, 0.4, 1.7));
      vehicleGroup.add(createWheelMesh(-1.12, 0.4, -1.7));
      vehicleGroup.add(createWheelMesh(1.12, 0.4, -1.7));

      // Headlights & Taillights
      const hlL = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.18, 0.08), headlightMat);
      hlL.position.set(-0.8, 0.7, 2.82);
      const hlR = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.18, 0.08), headlightMat);
      hlR.position.set(0.8, 0.7, 2.82);
      vehicleGroup.add(hlL, hlR);
      break;
    }

    case 'fire_engine': {
      // Heavy red fire truck
      const fireBodyGeo = new THREE.BoxGeometry(2.6, 2.3, 9.2);
      const fireMat = new THREE.MeshStandardMaterial({ color: 0xb91c1c, roughness: 0.3, metalness: 0.5 });
      const fBody = new THREE.Mesh(fireBodyGeo, fireMat);
      fBody.position.y = 1.5;
      fBody.castShadow = true;
      vehicleGroup.add(fBody);

      // Silver ladder rack
      const ladderGeo = new THREE.BoxGeometry(1.2, 0.2, 7.8);
      const ladderMat = new THREE.MeshStandardMaterial({ color: 0xe2e8f0, metalness: 0.9, roughness: 0.2 });
      const ladder = new THREE.Mesh(ladderGeo, ladderMat);
      ladder.position.set(0, 2.75, -0.4);
      vehicleGroup.add(ladder);

      // Cab lightbar
      const redStrobe = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.22, 0.35), sirenRedMat);
      redStrobe.position.set(0, 2.75, 3.2);
      vehicleGroup.add(redStrobe);

      // 6 Wheels
      vehicleGroup.add(createWheelMesh(-1.32, 0.48, 3.2));
      vehicleGroup.add(createWheelMesh(1.32, 0.48, 3.2));
      vehicleGroup.add(createWheelMesh(-1.32, 0.48, -2.2));
      vehicleGroup.add(createWheelMesh(1.32, 0.48, -2.2));
      vehicleGroup.add(createWheelMesh(-1.32, 0.48, -3.6));
      vehicleGroup.add(createWheelMesh(1.32, 0.48, -3.6));

      // Headlights
      const hlL = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.22, 0.1), headlightMat);
      hlL.position.set(-0.9, 0.75, 4.62);
      const hlR = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.22, 0.1), headlightMat);
      hlR.position.set(0.9, 0.75, 4.62);
      vehicleGroup.add(hlL, hlR);
      break;
    }
  }

  return vehicleGroup;
}
