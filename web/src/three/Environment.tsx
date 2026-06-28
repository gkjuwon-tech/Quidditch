import { useEffect } from "react";
import { useThree } from "@react-three/fiber";
import * as THREE from "three";
import { SUN_DIR, SKY } from "./scene";

// Builds an HDR-ish sunset environment that matches the sky dome and feeds it to
// scene.environment via PMREM. This is what gives the brass ferrule, the
// varnished handle's clearcoat and the snow caps real image-based reflections
// instead of flat shading — no external .hdr download required.
function buildEquirect() {
  const w = 512;
  const h = 256;
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  const ctx = c.getContext("2d")!;
  const img = ctx.createImageData(w, h);

  const sun = SUN_DIR.clone().normalize();
  const zenith = SKY.zenith;
  const horizon = SKY.horizon;
  const ground = SKY.ground;
  const sunCol = SKY.sun;
  const col = new THREE.Color();
  const tmp = new THREE.Color();

  for (let y = 0; y < h; y++) {
    const lat = (0.5 - y / h) * Math.PI; // +pi/2 (up) .. -pi/2 (down)
    const cl = Math.cos(lat);
    const sl = Math.sin(lat);
    for (let x = 0; x < w; x++) {
      const lon = (x / w) * 2 * Math.PI - Math.PI;
      const dx = cl * Math.sin(lon);
      const dy = sl;
      const dz = cl * Math.cos(lon);
      const mu = Math.max(dx * sun.x + dy * sun.y + dz * sun.z, 0);

      const up = THREE.MathUtils.clamp(dy, 0, 1);
      // sky: warm gold low, deepening violet up high
      col.copy(horizon).lerp(zenith, Math.pow(up, 0.5));
      const lowGlow = Math.exp(-up * 4.5);
      tmp.copy(sunCol).multiplyScalar(1.1).add(tmp.clone().copy(horizon).multiplyScalar(0));
      col.lerp(
        tmp.copy(sunCol).multiplyScalar(1.1).lerp(horizon, 0.3),
        lowGlow * (0.55 + 0.45 * Math.pow(mu, 0.8)),
      );
      // ground below the horizon
      if (dy < 0) {
        const g = THREE.MathUtils.clamp(-dy * 1.7, 0, 1);
        col.lerp(ground, g);
      }
      // sun disc + glow
      const glow = Math.pow(mu, 3) * 0.18 + Math.pow(mu, 14) * 0.55 + Math.pow(mu, 220) * 2.2;
      col.add(tmp.copy(sunCol).multiplyScalar(glow));

      const i = (y * w + x) * 4;
      img.data[i] = THREE.MathUtils.clamp(col.r, 0, 1) * 255;
      img.data[i + 1] = THREE.MathUtils.clamp(col.g, 0, 1) * 255;
      img.data[i + 2] = THREE.MathUtils.clamp(col.b, 0, 1) * 255;
      img.data[i + 3] = 255;
    }
  }
  ctx.putImageData(img, 0, 0);
  const tex = new THREE.CanvasTexture(c);
  tex.mapping = THREE.EquirectangularReflectionMapping;
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

export default function Environment() {
  const gl = useThree((s) => s.gl);
  const scene = useThree((s) => s.scene);

  useEffect(() => {
    const equirect = buildEquirect();
    const pmrem = new THREE.PMREMGenerator(gl);
    pmrem.compileEquirectangularShader();
    const env = pmrem.fromEquirectangular(equirect).texture;
    const prev = scene.environment;
    scene.environment = env;
    equirect.dispose();
    pmrem.dispose();
    return () => {
      scene.environment = prev;
      env.dispose();
    };
  }, [gl, scene]);

  return null;
}
