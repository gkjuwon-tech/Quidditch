import { useEffect, useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { makeWood, makeBrass, makeLeather } from "./textures";

// Fully procedural flying broom, pushed for a more believable, "real" read:
//  - a gently bent, varnished, tapered handle (swept tube + clearcoat)
//  - a turned brass ferrule + wound leather grip near the tail
//  - a dense teardrop of ~420 thin, tapered, splayed straws with colour variance
// No external mesh — everything is generated at mount.

const HANDLE_PTS = [
  new THREE.Vector3(0, 0, -1.62),
  new THREE.Vector3(0.02, 0.05, -0.6),
  new THREE.Vector3(0.0, 0.02, 0.6),
  new THREE.Vector3(-0.05, 0.2, 1.9),
  new THREE.Vector3(-0.07, 0.46, 2.62),
];

function useHandle() {
  return useMemo(() => {
    const curve = new THREE.CatmullRomCurve3(HANDLE_PTS);
    const steps = 240;
    const radial = 16;
    const geo = new THREE.TubeGeometry(curve, steps, 0.05, radial, false);
    const pos = geo.attributes.position as THREE.BufferAttribute;
    const tmp = new THREE.Vector3();
    for (let i = 0; i <= steps; i++) {
      const t = i / steps;
      // thick just above the bristles, swelling slightly, then thin to the grip
      const radius = THREE.MathUtils.lerp(0.072, 0.026, Math.pow(t, 0.85));
      const c = curve.getPointAt(t);
      for (let j = 0; j <= radial; j++) {
        const idx = i * (radial + 1) + j;
        tmp.set(pos.getX(idx), pos.getY(idx), pos.getZ(idx)).sub(c);
        tmp.setLength(radius);
        tmp.add(c);
        pos.setXYZ(idx, tmp.x, tmp.y, tmp.z);
      }
    }
    pos.needsUpdate = true;
    geo.computeVertexNormals();
    return geo;
  }, []);
}

// one tapered, slightly-bent straw, instanced many times
function useBristleGeo() {
  return useMemo(() => {
    const curve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(0, 0, 0),
      new THREE.Vector3(0.015, 0.34, 0),
      new THREE.Vector3(0.05, 0.68, 0),
      new THREE.Vector3(0.12, 1.0, 0),
    ]);
    const steps = 12;
    const radial = 5;
    const geo = new THREE.TubeGeometry(curve, steps, 0.013, radial, false);
    const pos = geo.attributes.position as THREE.BufferAttribute;
    const tmp = new THREE.Vector3();
    for (let i = 0; i <= steps; i++) {
      const t = i / steps;
      const radius = THREE.MathUtils.lerp(0.018, 0.002, t);
      const c = curve.getPointAt(t);
      for (let j = 0; j <= radial; j++) {
        const idx = i * (radial + 1) + j;
        tmp.set(pos.getX(idx), pos.getY(idx), pos.getZ(idx)).sub(c);
        tmp.setLength(radius);
        tmp.add(c);
        pos.setXYZ(idx, tmp.x, tmp.y, tmp.z);
      }
    }
    pos.needsUpdate = true;
    geo.computeVertexNormals();
    return geo;
  }, []);
}

function Bristles() {
  const ref = useRef<THREE.InstancedMesh>(null);
  const COUNT = 420;
  const geo = useBristleGeo();
  const mat = useMemo(
    () =>
      new THREE.MeshPhysicalMaterial({
        roughness: 0.78,
        metalness: 0,
        vertexColors: true,
        sheen: 0.6,
        sheenRoughness: 0.55,
        sheenColor: new THREE.Color("#ffdca0"),
        envMapIntensity: 0.5,
      }),
    [],
  );

  useEffect(() => {
    const mesh = ref.current;
    if (!mesh) return;
    const dummy = new THREE.Object3D();
    const up = new THREE.Vector3(0, 1, 0);
    const dir = new THREE.Vector3();
    const q = new THREE.Quaternion();
    const jitter = new THREE.Quaternion();
    const cDark = new THREE.Color("#5e3712");
    const cStraw = new THREE.Color("#caa15a");
    const cPale = new THREE.Color("#e6c585");
    const col = new THREE.Color();
    for (let i = 0; i < COUNT; i++) {
      // two shells: a tight inner core and a slightly wider outer wrap. The
      // straws stream BACKWARD along the shaft (−z) into a tapered tail, not a
      // radial ball — with a touch of droop so it reads like a real broom.
      const outer = i > COUNT * 0.42;
      const a = Math.random() * Math.PI * 2;
      const rad = Math.pow(Math.random(), 0.6) * (outer ? 0.26 : 0.13);
      const splay = (outer ? 0.2 : 0.1) + rad * 0.7;
      dir.set(Math.cos(a) * splay, Math.sin(a) * splay - 0.12, -1).normalize();
      q.setFromUnitVectors(up, dir);
      // small random tilt so straws don't look mathematically perfect
      jitter.setFromEuler(
        new THREE.Euler(
          (Math.random() - 0.5) * 0.18,
          Math.random() * Math.PI * 2,
          (Math.random() - 0.5) * 0.18,
        ),
      );
      q.multiply(jitter);
      const len = (outer ? 1.8 : 1.35) + Math.random() * 0.5 - rad * 0.8;
      dummy.position.set(Math.cos(a) * rad * 0.45, Math.sin(a) * rad * 0.45, -1.6);
      dummy.quaternion.copy(q);
      dummy.scale.set(1, len, 1);
      dummy.updateMatrix();
      mesh.setMatrixAt(i, dummy.matrix);
      const m = Math.random();
      col.copy(cDark).lerp(m > 0.5 ? cPale : cStraw, Math.random() * 0.85 + 0.1);
      mesh.setColorAt(i, col);
    }
    mesh.instanceMatrix.needsUpdate = true;
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
  }, [COUNT]);

  return <instancedMesh ref={ref} args={[geo, mat, COUNT]} castShadow />;
}

export default function Broom() {
  const group = useRef<THREE.Group>(null);
  const handle = useHandle();

  const wood = useMemo(() => {
    const { map, roughnessMap, normalMap } = makeWood();
    return new THREE.MeshPhysicalMaterial({
      map,
      roughnessMap,
      normalMap,
      normalScale: new THREE.Vector2(0.5, 0.5),
      color: new THREE.Color("#caa074"),
      roughness: 1.0,
      metalness: 0.0,
      clearcoat: 0.85,
      clearcoatRoughness: 0.28,
      sheen: 0.25,
      sheenColor: new THREE.Color("#ffce9a"),
      anisotropy: 0.6,
      anisotropyRotation: Math.PI / 2,
      envMapIntensity: 1.0,
    });
  }, []);
  const brass = useMemo(() => {
    const { roughnessMap, normalMap } = makeBrass();
    return new THREE.MeshStandardMaterial({
      roughnessMap,
      normalMap,
      normalScale: new THREE.Vector2(0.4, 0.4),
      color: new THREE.Color("#c0964c"),
      roughness: 0.42,
      metalness: 1.0,
      envMapIntensity: 1.0,
    });
  }, []);
  const leather = useMemo(() => {
    const { map, normalMap } = makeLeather();
    return new THREE.MeshStandardMaterial({
      map,
      normalMap,
      normalScale: new THREE.Vector2(0.8, 0.8),
      roughness: 0.74,
      metalness: 0.0,
      envMapIntensity: 0.6,
    });
  }, []);

  useFrame((s) => {
    const t = s.clock.elapsedTime;
    if (group.current) {
      // profile pose: shaft lies across the view (grip forward-right, tail
      // trailing back-left), nose tilted up like it's in flight.
      group.current.position.y = 1.0 + Math.sin(t * 0.6) * 0.12;
      group.current.rotation.z = -0.34 + Math.sin(t * 0.32) * 0.02;
      group.current.rotation.x = 0.1 + Math.cos(t * 0.4) * 0.02;
      group.current.rotation.y = 1.2 + Math.sin(t * 0.18) * 0.04;
    }
  });

  return (
    <group ref={group} position={[0, 1.08, 0]}>
      <mesh geometry={handle} material={wood} castShadow receiveShadow />

      {/* brass ferrule binding the straws to the shaft */}
      <mesh position={[0, 0.01, -1.46]} rotation={[Math.PI / 2, 0, 0]} material={brass}>
        <cylinderGeometry args={[0.088, 0.082, 0.2, 22]} />
      </mesh>
      <mesh position={[0, 0.01, -1.3]} rotation={[Math.PI / 2, 0, 0]} material={brass}>
        <torusGeometry args={[0.085, 0.014, 12, 24]} />
      </mesh>

      {/* wound leather grip near the tail */}
      {[2.04, 2.18, 2.32, 2.46].map((z, i) => (
        <mesh
          key={z}
          position={[-0.05, 0.34 + i * 0.04, z]}
          rotation={[Math.PI / 2.1, 0, 0]}
          material={leather}
        >
          <torusGeometry args={[0.045, 0.013, 10, 20]} />
        </mesh>
      ))}
      {/* hanging strap loop at the very tip */}
      <mesh position={[-0.07, 0.5, 2.66]} rotation={[0, 0, 0.3]} material={leather}>
        <torusGeometry args={[0.07, 0.011, 10, 24]} />
      </mesh>

      <Bristles />
    </group>
  );
}
