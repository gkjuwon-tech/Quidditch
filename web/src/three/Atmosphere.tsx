import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { atmosphereVert, atmosphereFrag } from "./glsl";

export default function Atmosphere({
  position = [0, -1, -6] as [number, number, number],
  scale = [40, 22, 1] as [number, number, number],
  color = "#cdd6e6",
  opacity = 0.5,
}) {
  const matRef = useRef<THREE.ShaderMaterial>(null);
  const uniforms = useMemo(
    () => ({
      uTime: { value: 0 },
      uColor: { value: new THREE.Color(color) },
      uOpacity: { value: opacity },
    }),
    [color, opacity],
  );

  useFrame((_, dt) => {
    if (matRef.current) matRef.current.uniforms.uTime.value += dt;
  });

  return (
    <mesh position={position} scale={scale}>
      <planeGeometry args={[1, 1, 1, 1]} />
      <shaderMaterial
        ref={matRef}
        uniforms={uniforms}
        vertexShader={atmosphereVert}
        fragmentShader={atmosphereFrag}
        transparent
        depthWrite={false}
      />
    </mesh>
  );
}
