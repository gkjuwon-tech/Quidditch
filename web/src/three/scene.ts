import * as THREE from "three";

// Shared golden-hour scene configuration so the sky, the key light and the
// fog all agree on where the sun is and what colour the air is.
export const SUN_DIR = new THREE.Vector3(-0.42, 0.14, -1).normalize();

export const SKY = {
  zenith: new THREE.Color(0.11, 0.14, 0.34),
  horizon: new THREE.Color(1.15, 0.56, 0.32),
  ground: new THREE.Color(0.06, 0.05, 0.06),
  sun: new THREE.Color(1.3, 0.68, 0.36),
};

// Horizon colour drives the fog so distant ridges melt into the sky.
export const FOG_COLOR = new THREE.Color(0.66, 0.42, 0.36);
