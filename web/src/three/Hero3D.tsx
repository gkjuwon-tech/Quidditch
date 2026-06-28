import { useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import {
  Environment,
  Text,
  AdaptiveDpr,
  Preload,
} from "@react-three/drei";
import * as THREE from "three";
import { Ridge, Cliff } from "./Models";
import Broom from "./Broom";
import Embers from "./Embers";
import Atmosphere from "./Atmosphere";

function CameraRig() {
  const { camera, pointer } = useThree();
  const target = useRef(new THREE.Vector3(0, 0, 0));
  useFrame((state, dt) => {
    const t = state.clock.elapsedTime;
    const px = pointer.x * 1.2 + Math.sin(t * 0.15) * 0.3;
    const py = pointer.y * 0.6 + Math.cos(t * 0.12) * 0.2;
    camera.position.x += (px - camera.position.x) * Math.min(1, dt * 1.5);
    camera.position.y += (0.8 + py - camera.position.y) * Math.min(1, dt * 1.5);
    camera.lookAt(target.current);
  });
  return null;
}

export default function Hero3D() {
  return (
    <>
      <color attach="background" args={["#0a0c12"]} />
      <fog attach="fog" args={["#10131c", 18, 70]} />

      <CameraRig />

      {/* dramatic CC0 mountain sky, lights the whole scene */}
      <Environment files="/hdri/sky_mountain_2k.hdr" background blur={0.06} />

      <ambientLight intensity={0.2} />
      <directionalLight
        position={[6, 9, 4]}
        intensity={2.4}
        color="#ffe6b0"
        castShadow
      />
      <directionalLight position={[-8, 2, -6]} intensity={0.6} color="#6f86c4" />

      {/* real 3D terrain — distant ridge + foreground cliff */}
      <Ridge />
      <Cliff />

      {/* in-scene headline — the broom crosses in front of it */}
      <group position={[0, 0.7, 0]}>
        <Text
          font="/fonts/Cinzel.ttf"
          fontSize={1.62}
          position={[0, 0.95, 0]}
          anchorX="center"
          anchorY="middle"
          letterSpacing={0.05}
          color="#f1ead9"
          outlineWidth={0.005}
          outlineColor="#000000"
          outlineOpacity={0.4}
        >
          QUIDDITCH
        </Text>
        <Text
          font="/fonts/Cinzel.ttf"
          fontSize={1.62}
          position={[0, -0.95, 0]}
          anchorX="center"
          anchorY="middle"
          letterSpacing={0.18}
          color="#f4d27a"
        >
          IS REAL
        </Text>
      </group>

      <Atmosphere position={[0, -3.5, -3]} scale={[60, 22, 1]} opacity={0.5} />
      <Broom />
      <Embers />

      <AdaptiveDpr pixelated />
      <Preload all />
    </>
  );
}
