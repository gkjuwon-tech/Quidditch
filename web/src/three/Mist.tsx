import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { atmosphereVert, atmosphereFrag } from "./glsl";
import { FOG_COLOR, SKY } from "./scene";

// Volumetric-looking haze: open cylinders wrapping the scene, shaded with a
// drifting two-layer noise so distant ridges sit in real, billowy mist instead
// of a flat uniform fog wash. A low ground band + a taller ridge band.
function MistBand({
  radius,
  height,
  y,
  color,
  opacity,
  speed,
}: {
  radius: number;
  height: number;
  y: number;
  color: THREE.Color;
  opacity: number;
  speed: number;
}) {
  const mat = useRef<THREE.ShaderMaterial>(null);
  const uniforms = useMemo(
    () => ({
      uTime: { value: 0 },
      uColor: { value: color.clone() },
      uOpacity: { value: opacity },
    }),
    [color, opacity],
  );
  useFrame((s) => {
    if (mat.current) mat.current.uniforms.uTime.value = s.clock.elapsedTime * speed;
  });
  return (
    <mesh position={[0, y, 0]} frustumCulled={false}>
      <cylinderGeometry args={[radius, radius, height, 96, 1, true]} />
      <shaderMaterial
        ref={mat}
        vertexShader={atmosphereVert}
        fragmentShader={atmosphereFrag}
        uniforms={uniforms}
        side={THREE.BackSide}
        transparent
        depthWrite={false}
        fog={false}
      />
    </mesh>
  );
}

export default function Mist() {
  const ridge = useMemo(() => FOG_COLOR.clone().lerp(SKY.sun, 0.25), []);
  const ground = useMemo(() => FOG_COLOR.clone().multiplyScalar(0.8), []);
  return (
    <group>
      {/* thin haze hugging the far ridge bases, letting the peaks rise above */}
      <MistBand radius={300} height={70} y={-6} color={ridge} opacity={0.3} speed={1} />
      <MistBand radius={170} height={42} y={-8} color={ridge} opacity={0.24} speed={1.4} />
      {/* low ground fog rolling across the plateau under the broom */}
      <MistBand radius={80} height={16} y={-10} color={ground} opacity={0.28} speed={1.8} />
    </group>
  );
}
