// 3D simplex noise — public domain / MIT.
// Author: Ian McEwan, Ashima Arts; Stefan Gustavson.
// https://github.com/ashima/webgl-noise  (battle-tested, used across the industry)
export const SIMPLEX_NOISE = /* glsl */ `
vec4 permute(vec4 x){return mod(((x*34.0)+1.0)*x, 289.0);}
vec4 taylorInvSqrt(vec4 r){return 1.79284291400159 - 0.85373472095314 * r;}

float snoise(vec3 v){
  const vec2  C = vec2(1.0/6.0, 1.0/3.0);
  const vec4  D = vec4(0.0, 0.5, 1.0, 2.0);
  vec3 i  = floor(v + dot(v, C.yyy));
  vec3 x0 = v - i + dot(i, C.xxx);
  vec3 g = step(x0.yzx, x0.xyz);
  vec3 l = 1.0 - g;
  vec3 i1 = min(g.xyz, l.zxy);
  vec3 i2 = max(g.xyz, l.zxy);
  vec3 x1 = x0 - i1 + 1.0 * C.xxx;
  vec3 x2 = x0 - i2 + 2.0 * C.xxx;
  vec3 x3 = x0 - 1.0 + 3.0 * C.xxx;
  i = mod(i, 289.0);
  vec4 p = permute(permute(permute(
            i.z + vec4(0.0, i1.z, i2.z, 1.0))
          + i.y + vec4(0.0, i1.y, i2.y, 1.0))
          + i.x + vec4(0.0, i1.x, i2.x, 1.0));
  float n_ = 1.0/7.0;
  vec3  ns = n_ * D.wyz - D.xzx;
  vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
  vec4 x_ = floor(j * ns.z);
  vec4 y_ = floor(j - 7.0 * x_);
  vec4 x = x_ * ns.x + ns.yyyy;
  vec4 y = y_ * ns.x + ns.yyyy;
  vec4 h = 1.0 - abs(x) - abs(y);
  vec4 b0 = vec4(x.xy, y.xy);
  vec4 b1 = vec4(x.zw, y.zw);
  vec4 s0 = floor(b0) * 2.0 + 1.0;
  vec4 s1 = floor(b1) * 2.0 + 1.0;
  vec4 sh = -step(h, vec4(0.0));
  vec4 a0 = b0.xzyw + s0.xzyw * sh.xxyy;
  vec4 a1 = b1.xzyw + s1.xzyw * sh.zzww;
  vec3 p0 = vec3(a0.xy, h.x);
  vec3 p1 = vec3(a0.zw, h.y);
  vec3 p2 = vec3(a1.xy, h.z);
  vec3 p3 = vec3(a1.zw, h.w);
  vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
  p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
  vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
  m = m * m;
  return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
}
`;

// Atmospheric mist drifting in front of the ridge.
export const atmosphereVert = /* glsl */ `
varying vec2 vUv;
void main(){
  vUv = uv;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;

export const atmosphereFrag = /* glsl */ `
varying vec2 vUv;
uniform float uTime;
uniform vec3 uColor;
uniform float uOpacity;
${SIMPLEX_NOISE}

float fbm(vec3 p){
  float v = 0.0;
  float a = 0.5;
  for(int i=0;i<5;i++){
    v += a * snoise(p);
    p *= 2.0;
    a *= 0.5;
  }
  return v;
}

void main(){
  vec2 uv = vUv;
  float t = uTime * 0.025;
  float n = fbm(vec3(uv * 2.4 + vec2(t, t * 0.3), t * 0.6));
  n = 0.5 + 0.5 * n;
  // mist sits low and feathers upward
  float band = smoothstep(0.0, 0.55, uv.y) * (1.0 - smoothstep(0.45, 1.0, uv.y));
  float density = pow(n, 1.8) * band;
  // soft horizontal edges
  density *= smoothstep(0.0, 0.18, uv.x) * (1.0 - smoothstep(0.82, 1.0, uv.x));
  gl_FragColor = vec4(uColor, density * uOpacity);
}
`;

// Floating gold embers / magic dust.
export const emberVert = /* glsl */ `
uniform float uTime;
uniform float uPixelRatio;
attribute float aScale;
attribute float aSpeed;
attribute float aPhase;
varying float vAlpha;
${SIMPLEX_NOISE}

void main(){
  vec3 pos = position;
  float t = uTime * aSpeed;
  // gentle rise + lateral drift driven by noise
  pos.y = mod(pos.y + t * 0.6, 18.0) - 9.0;
  pos.x += snoise(vec3(pos.y * 0.15, aPhase, t * 0.2)) * 1.4;
  pos.z += snoise(vec3(aPhase, pos.y * 0.15, t * 0.2)) * 1.0;

  vec4 mv = modelViewMatrix * vec4(pos, 1.0);
  float twinkle = 0.5 + 0.5 * sin(t * 3.0 + aPhase * 6.28);
  vAlpha = twinkle * smoothstep(9.0, 4.0, abs(pos.y));
  gl_PointSize = aScale * uPixelRatio * (140.0 / -mv.z) * (0.6 + twinkle * 0.6);
  gl_Position = projectionMatrix * mv;
}
`;

export const emberFrag = /* glsl */ `
uniform vec3 uColor;
varying float vAlpha;
void main(){
  vec2 c = gl_PointCoord - 0.5;
  float d = length(c);
  float glow = smoothstep(0.5, 0.0, d);
  float core = smoothstep(0.18, 0.0, d);
  vec3 col = mix(uColor, vec3(1.0, 0.95, 0.82), core);
  gl_FragColor = vec4(col, (glow * 0.55 + core) * vAlpha);
}
`;
