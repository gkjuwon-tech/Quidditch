import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { emberVert, emberFrag } from "./glsl";

export default function Embers({ count = 340 }: { count?: number }) {
  const matRef = useRef<THREE.ShaderMaterial>(null);

  const geo = useMemo(() => {
    const positions = new Float32Array(count * 3);
    const scale = new Float32Array(count);
    const speed = new Float32Array(count);
    const phase = new Float32Array(count);
    for (let i = 0; i < count; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 28;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 16;
      // keep motes off the camera's lap so none balloon into a near blob
      positions[i * 3 + 2] = (Math.random() - 0.5) * 15 - 5;
      // mostly fine dust, with only a few slightly larger motes
      scale[i] = 0.28 + Math.pow(Math.random(), 2.2) * 0.85;
      speed[i] = 0.35 + Math.random() * 0.8;
      phase[i] = Math.random() * 6.283;
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    g.setAttribute("aScale", new THREE.BufferAttribute(scale, 1));
    g.setAttribute("aSpeed", new THREE.BufferAttribute(speed, 1));
    g.setAttribute("aPhase", new THREE.BufferAttribute(phase, 1));
    return g;
  }, [count]);

  const uniforms = useMemo(
    () => ({
      uTime: { value: 0 },
      uPixelRatio: { value: Math.min(window.devicePixelRatio, 2) },
      uColor: { value: new THREE.Color("#e8c184") },
    }),
    [],
  );

  useFrame((_, dt) => {
    if (matRef.current) matRef.current.uniforms.uTime.value += dt;
  });

  return (
    <points geometry={geo} frustumCulled={false}>
      <shaderMaterial
        ref={matRef}
        uniforms={uniforms}
        vertexShader={emberVert}
        fragmentShader={emberFrag}
        transparent
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </points>
  );
}
