import { useMemo, useRef } from "react";
import { useGLTF } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

// The NIMBUS broom — real CC0 GLB, floating in front of the headline so the
// type is partially eclipsed by it (depth-correct occlusion).
export default function Broom() {
  const { scene } = useGLTF("/models/plastic_broom.glb");
  const group = useRef<THREE.Group>(null);
  const inner = useRef<THREE.Group>(null);

  const model = useMemo(() => {
    const clone = scene.clone(true);
    const box = new THREE.Box3().setFromObject(clone);
    const size = new THREE.Vector3();
    const center = new THREE.Vector3();
    box.getSize(size);
    box.getCenter(center);
    const maxDim = Math.max(size.x, size.y, size.z) || 1;
    const s = 4.6 / maxDim;
    clone.scale.setScalar(s);
    clone.position.set(-center.x * s, -center.y * s, -center.z * s);
    clone.traverse((o) => {
      if ((o as THREE.Mesh).isMesh) {
        const m = (o as THREE.Mesh).material as THREE.MeshStandardMaterial;
        if (m) {
          m.envMapIntensity = 1.1;
          m.roughness = Math.min(m.roughness ?? 0.6, 0.55);
        }
      }
    });
    return clone;
  }, [scene]);

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    if (group.current) {
      group.current.position.y = 0.4 + Math.sin(t * 0.6) * 0.22;
      group.current.position.x = 1.0 + Math.sin(t * 0.3) * 0.3;
    }
    if (inner.current) {
      inner.current.rotation.z = -0.78 + Math.sin(t * 0.4) * 0.05;
      inner.current.rotation.y = 0.3 + Math.sin(t * 0.18) * 0.3;
      inner.current.rotation.x = 0.1 + Math.cos(t * 0.5) * 0.05;
    }
  });

  return (
    <group ref={group} position={[1.0, 0.4, 3.6]}>
      <group ref={inner}>
        <primitive object={model} />
      </group>
    </group>
  );
}

useGLTF.preload("/models/plastic_broom.glb");
