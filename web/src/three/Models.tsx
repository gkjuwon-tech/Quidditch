import { useMemo } from "react";
import { useGLTF } from "@react-three/drei";
import * as THREE from "three";

// Clone a loaded scene and normalize it: centered at origin, sized so its
// largest dimension equals `targetSize` world units.
function useNormalized(url: string, targetSize: number) {
  const { scene } = useGLTF(url);
  return useMemo(() => {
    const clone = scene.clone(true);
    const box = new THREE.Box3().setFromObject(clone);
    const size = new THREE.Vector3();
    const center = new THREE.Vector3();
    box.getSize(size);
    box.getCenter(center);
    const maxDim = Math.max(size.x, size.y, size.z) || 1;
    const s = targetSize / maxDim;
    clone.scale.setScalar(s);
    clone.position.set(-center.x * s, -center.y * s, -center.z * s);
    clone.traverse((o) => {
      if ((o as THREE.Mesh).isMesh) {
        o.castShadow = true;
        o.receiveShadow = true;
        const m = (o as THREE.Mesh).material as THREE.MeshStandardMaterial;
        if (m) m.envMapIntensity = 0.7;
      }
    });
    const g = new THREE.Group();
    g.add(clone);
    return g;
  }, [scene, targetSize]);
}

export function Ridge() {
  const mtn = useNormalized("/models/mountainside.glb", 26);
  // A distant ridge: slabs of real mountain geometry, low on the horizon and
  // pushed far back so the dramatic CC0 sky and the headline can breathe.
  const layout: Array<[number, number, number, number, number]> = [
    // x, y, z, rotY, scale
    [-30, -16, -58, 0.4, 1.3],
    [10, -19, -70, -0.7, 1.7],
    [34, -15, -52, 1.9, 1.1],
  ];
  return (
    <group>
      {layout.map(([x, y, z, ry, sc], i) => (
        <primitive
          key={i}
          object={i === 0 ? mtn : mtn.clone(true)}
          position={[x, y, z]}
          rotation={[0, ry, 0]}
          scale={sc}
        />
      ))}
    </group>
  );
}

export function Cliff() {
  const cliff = useNormalized("/models/coastal_cliff_02.glb", 9);
  // Foreground outcrop, bottom-left corner, anchoring the composition.
  return (
    <primitive
      object={cliff}
      position={[-13.5, -9.5, -7]}
      rotation={[0, 0.7, 0.05]}
      scale={1.1}
    />
  );
}

useGLTF.preload("/models/mountainside.glb");
useGLTF.preload("/models/coastal_cliff_02.glb");
