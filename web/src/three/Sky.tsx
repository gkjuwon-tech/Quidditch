import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { skyVert, skyFrag } from "./glsl";
import { SUN_DIR, SKY } from "./scene";

// Procedural sunset dome — a big inside-out sphere shaded entirely in GLSL.
export default function Sky() {
  const mat = useRef<THREE.ShaderMaterial>(null);
  const uniforms = useMemo(
    () => ({
      uTime: { value: 0 },
      uSunDir: { value: SUN_DIR.clone() },
      uZenith: { value: SKY.zenith.clone() },
      uHorizon: { value: SKY.horizon.clone() },
      uGround: { value: SKY.ground.clone() },
      uSun: { value: SKY.sun.clone() },
    }),
    [],
  );

  useFrame((s) => {
    if (mat.current) mat.current.uniforms.uTime.value = s.clock.elapsedTime;
  });

  return (
    <mesh scale={600} frustumCulled={false}>
      <sphereGeometry args={[1, 64, 32]} />
      <shaderMaterial
        ref={mat}
        vertexShader={skyVert}
        fragmentShader={skyFrag}
        uniforms={uniforms}
        side={THREE.BackSide}
        depthWrite={false}
        toneMapped
        fog={false}
      />
    </mesh>
  );
}
