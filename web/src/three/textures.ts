import * as THREE from "three";

// Tiny, deterministic value-noise so the procedural maps are stable between
// reloads (no flicker) and don't need any external texture files.
function makeNoise(seed: number) {
  const hash = (x: number, y: number) => {
    const s = Math.sin(x * 127.1 + y * 311.7 + seed * 74.7) * 43758.5453;
    return s - Math.floor(s);
  };
  const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
  const smooth = (t: number) => t * t * (3 - 2 * t);
  const value = (x: number, y: number) => {
    const xi = Math.floor(x);
    const yi = Math.floor(y);
    const xf = x - xi;
    const yf = y - yi;
    const u = smooth(xf);
    const v = smooth(yf);
    const a = hash(xi, yi);
    const b = hash(xi + 1, yi);
    const c = hash(xi, yi + 1);
    const d = hash(xi + 1, yi + 1);
    return lerp(lerp(a, b, u), lerp(c, d, u), v);
  };
  return (x: number, y: number, octaves = 4) => {
    let amp = 0.5;
    let freq = 1;
    let sum = 0;
    let norm = 0;
    for (let o = 0; o < octaves; o++) {
      sum += amp * value(x * freq, y * freq);
      norm += amp;
      amp *= 0.5;
      freq *= 2.03;
    }
    return sum / norm;
  };
}

function canvas(size: number) {
  const c = document.createElement("canvas");
  c.width = size;
  c.height = size;
  return { c, ctx: c.getContext("2d")! };
}

function toTexture(c: HTMLCanvasElement, repeatX = 1, repeatY = 1) {
  const t = new THREE.CanvasTexture(c);
  t.wrapS = THREE.RepeatWrapping;
  t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(repeatX, repeatY);
  t.anisotropy = 8;
  return t;
}

// Derive a tangent-space normal map from a grayscale height canvas (Sobel).
function normalFromHeight(src: HTMLCanvasElement, strength: number) {
  const size = src.width;
  const sctx = src.getContext("2d")!;
  const h = sctx.getImageData(0, 0, size, size).data;
  const { c, ctx } = canvas(size);
  const out = ctx.createImageData(size, size);
  const at = (x: number, y: number) => {
    const xi = (x + size) % size;
    const yi = (y + size) % size;
    return h[(yi * size + xi) * 4] / 255;
  };
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const dx = (at(x - 1, y) - at(x + 1, y)) * strength;
      const dy = (at(x, y - 1) - at(x, y + 1)) * strength;
      const len = Math.hypot(dx, dy, 1);
      const i = (y * size + x) * 4;
      out.data[i] = ((dx / len) * 0.5 + 0.5) * 255;
      out.data[i + 1] = ((dy / len) * 0.5 + 0.5) * 255;
      out.data[i + 2] = (1 / len) * 255;
      out.data[i + 3] = 255;
    }
  }
  ctx.putImageData(out, 0, 0);
  return c;
}

// ---------------------------------------------------------------- VARNISHED WOOD
// Lengthwise grain with knots and fine fibre, plus matching roughness + normal
// so the handle reads as a turned, oiled hardwood instead of a plastic tube.
export function makeWood() {
  const size = 512;
  const noise = makeNoise(7.7);
  const { c, ctx } = canvas(size);
  const height = canvas(size);
  const rough = canvas(size);
  const cImg = ctx.createImageData(size, size);
  const hImg = height.ctx.createImageData(size, size);
  const rImg = rough.ctx.createImageData(size, size);

  const dark = new THREE.Color("#2b1708");
  const mid = new THREE.Color("#5a3414");
  const light = new THREE.Color("#8a572a");
  const col = new THREE.Color();

  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const u = x / size;
      const v = y / size;
      // domain warp so the rings/grain wobble like real timber
      const warp = noise(u * 3, v * 14, 4) * 0.5;
      // tight grain running along the handle (v axis) + a couple of knots
      let grain = Math.sin((u * 18 + warp * 6) * Math.PI * 2);
      grain = grain * 0.5 + 0.5;
      grain = Math.pow(grain, 1.6);
      const fibre = noise(u * 60, v * 6, 3);
      const knot = Math.pow(noise(u * 4 + 2, v * 4, 2), 6) * 1.4;
      let t = grain * 0.7 + fibre * 0.3;
      t = THREE.MathUtils.clamp(t - knot, 0, 1);

      col.copy(dark).lerp(mid, THREE.MathUtils.smoothstep(t, 0.1, 0.55));
      col.lerp(light, THREE.MathUtils.smoothstep(t, 0.55, 0.95) * 0.85);

      const i = (y * size + x) * 4;
      cImg.data[i] = col.r * 255;
      cImg.data[i + 1] = col.g * 255;
      cImg.data[i + 2] = col.b * 255;
      cImg.data[i + 3] = 255;

      const hv = THREE.MathUtils.clamp(t * 0.7 + fibre * 0.3 + knot * 0.4, 0, 1);
      hImg.data[i] = hImg.data[i + 1] = hImg.data[i + 2] = hv * 255;
      hImg.data[i + 3] = 255;

      // grain valleys hold more oil → glossier; knots stay matte
      const rv = THREE.MathUtils.clamp(0.32 + (1 - grain) * 0.28 + knot * 0.5, 0, 1);
      rImg.data[i] = rImg.data[i + 1] = rImg.data[i + 2] = rv * 255;
      rImg.data[i + 3] = 255;
    }
  }
  ctx.putImageData(cImg, 0, 0);
  height.ctx.putImageData(hImg, 0, 0);
  rough.ctx.putImageData(rImg, 0, 0);

  return {
    map: toTexture(c, 1, 4),
    roughnessMap: toTexture(rough.c, 1, 4),
    normalMap: toTexture(normalFromHeight(height.c, 2.2), 1, 4),
  };
}

// ---------------------------------------------------------------- BRUSHED BRASS
export function makeBrass() {
  const size = 256;
  const noise = makeNoise(3.1);
  const height = canvas(size);
  const rough = canvas(size);
  const hImg = height.ctx.createImageData(size, size);
  const rImg = rough.ctx.createImageData(size, size);
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      // fine circumferential brushing (along x) + faint patina blotches
      const brush = noise(x * 0.4, y * 8, 2);
      const patina = noise(x * 2, y * 2, 3);
      const i = (y * size + x) * 4;
      hImg.data[i] = hImg.data[i + 1] = hImg.data[i + 2] = brush * 255;
      hImg.data[i + 3] = 255;
      const rv = THREE.MathUtils.clamp(0.18 + brush * 0.14 + patina * 0.22, 0, 1);
      rImg.data[i] = rImg.data[i + 1] = rImg.data[i + 2] = rv * 255;
      rImg.data[i + 3] = 255;
    }
  }
  height.ctx.putImageData(hImg, 0, 0);
  rough.ctx.putImageData(rImg, 0, 0);
  return {
    roughnessMap: toTexture(rough.c, 1, 1),
    normalMap: toTexture(normalFromHeight(height.c, 1.1), 1, 1),
  };
}

// ---------------------------------------------------------------- WORN LEATHER
export function makeLeather() {
  const size = 256;
  const noise = makeNoise(9.4);
  const { c, ctx } = canvas(size);
  const height = canvas(size);
  const cImg = ctx.createImageData(size, size);
  const hImg = height.ctx.createImageData(size, size);
  const base = new THREE.Color("#2c1d12");
  const hi = new THREE.Color("#5a3c26");
  const col = new THREE.Color();
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const grain = noise(x * 0.6, y * 0.6, 4);
      const pores = noise(x * 6, y * 6, 2);
      const t = THREE.MathUtils.clamp(grain * 0.7 + pores * 0.3, 0, 1);
      col.copy(base).lerp(hi, t * 0.7);
      const i = (y * size + x) * 4;
      cImg.data[i] = col.r * 255;
      cImg.data[i + 1] = col.g * 255;
      cImg.data[i + 2] = col.b * 255;
      cImg.data[i + 3] = 255;
      hImg.data[i] = hImg.data[i + 1] = hImg.data[i + 2] = t * 255;
      hImg.data[i + 3] = 255;
    }
  }
  ctx.putImageData(cImg, 0, 0);
  height.ctx.putImageData(hImg, 0, 0);
  return {
    map: toTexture(c, 2, 1),
    normalMap: toTexture(normalFromHeight(height.c, 1.6), 2, 1),
  };
}

// ---------------------------------------------------------------- TERRAIN DETAIL
// A seamless-ish rocky detail used as a tiled roughness + normal break-up on the
// mountains so the ridges catch the low sun with real micro-relief.
export function makeTerrainDetail() {
  const size = 512;
  const noise = makeNoise(21.9);
  const height = canvas(size);
  const rough = canvas(size);
  const hImg = height.ctx.createImageData(size, size);
  const rImg = rough.ctx.createImageData(size, size);
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const u = x / size;
      const v = y / size;
      // ridged noise gives rocky creases
      let n = noise(u * 8, v * 8, 5);
      n = 1 - Math.abs(n * 2 - 1);
      const fine = noise(u * 40, v * 40, 2);
      const h = THREE.MathUtils.clamp(n * 0.7 + fine * 0.3, 0, 1);
      const i = (y * size + x) * 4;
      hImg.data[i] = hImg.data[i + 1] = hImg.data[i + 2] = h * 255;
      hImg.data[i + 3] = 255;
      const rv = THREE.MathUtils.clamp(0.7 + (1 - h) * 0.25, 0, 1);
      rImg.data[i] = rImg.data[i + 1] = rImg.data[i + 2] = rv * 255;
      rImg.data[i + 3] = 255;
    }
  }
  height.ctx.putImageData(hImg, 0, 0);
  rough.ctx.putImageData(rImg, 0, 0);
  return {
    roughnessMap: toTexture(rough.c, 18, 18),
    normalMap: toTexture(normalFromHeight(height.c, 1.5), 18, 18),
  };
}
