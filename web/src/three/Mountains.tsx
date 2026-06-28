import { useMemo } from "react";
import * as THREE from "three";
import { ImprovedNoise } from "three/examples/jsm/math/ImprovedNoise.js";

// A single procedurally displaced terrain: a calm plateau under the broom that
// rises into a 360° ring of ridged peaks, so an orbiting camera always has a
// dramatic dusk skyline. Heights + per-vertex colours (dark rock → warm,
// sunset-lit snow caps) are baked once with ridged fractal noise.
function buildTerrain() {
  const size = 1200;
  const seg = 360;
  const geo = new THREE.PlaneGeometry(size, size, seg, seg);
  const perlin = new ImprovedNoise();
  const pos = geo.attributes.position as THREE.BufferAttribute;
  const seed = 17.3;

  const rock = new THREE.Color("#2a1d1d");
  const rockHi = new THREE.Color("#574033");
  const snow = new THREE.Color("#f4e3d2");
  const snowWarm = new THREE.Color("#ffd2a0");
  const colors = new Float32Array(pos.count * 3);
  const c = new THREE.Color();

  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i);
    const y = pos.getY(i);
    const r = Math.hypot(x, y);

    // ridged multi-octave noise
    let amp = 1;
    let freq = 0.0016;
    let h = 0;
    for (let o = 0; o < 6; o++) {
      const n = perlin.noise(x * freq, y * freq, seed);
      h += (1 - Math.abs(n)) * amp;
      amp *= 0.5;
      freq *= 2.04;
    }
    h = Math.pow(h * 0.55, 2.2);

    const ring = THREE.MathUtils.smoothstep(r, 60, 280);
    const peak = 52 * ring;
    const valley = -5 + 3 * THREE.MathUtils.smoothstep(r, 0, 60);
    const z = valley + h * peak;
    pos.setZ(i, z);

    // colour by elevation: warm dark rock low, then snow on the high ridges,
    // with a little fine-grain mottling so it isn't a flat wash.
    const elev = THREE.MathUtils.clamp(z / 34, 0, 1);
    const mottle = perlin.noise(x * 0.02, y * 0.02, 4.1) * 0.12;
    c.copy(rock).lerp(rockHi, THREE.MathUtils.clamp(elev * 1.6 + mottle, 0, 1));
    const snowAmt = THREE.MathUtils.smoothstep(elev + mottle, 0.34, 0.62);
    const snowCol = snow.clone().lerp(snowWarm, 0.45 + mottle);
    c.lerp(snowCol, snowAmt);
    colors[i * 3] = c.r;
    colors[i * 3 + 1] = c.g;
    colors[i * 3 + 2] = c.b;
  }
  geo.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  geo.computeVertexNormals();
  return geo;
}

export default function Mountains() {
  const geo = useMemo(buildTerrain, []);
  const mat = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        vertexColors: true,
        roughness: 0.92,
        metalness: 0,
      }),
    [],
  );
  return (
    <mesh
      geometry={geo}
      material={mat}
      rotation={[-Math.PI / 2, 0, 0]}
      position={[0, -3, 0]}
      receiveShadow
    />
  );
}
