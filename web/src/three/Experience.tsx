import { useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import { useScroll } from "@react-three/drei";
import { EffectComposer, Bloom, Vignette } from "@react-three/postprocessing";
import * as THREE from "three";
import Sky from "./Sky";
import Env from "./Environment";
import Mountains from "./Mountains";
import Mist from "./Mist";
import Broom from "./Broom";
import Embers from "./Embers";
import { SUN_DIR } from "./scene";

// Scroll drives the camera. Through the hero (offset < ~0.12) it stays head-on
// with a slow dolly-in; past the hero it sweeps ~270° around the broom while
// dollying and rising with scroll. Reference framing is authored for a wide
// desktop viewport; on narrower / portrait screens we widen the (vertical) FOV
// so the broom keeps roughly the same composition it has on a PC instead of
// cropping in.
const REF_ASPECT = 1.6;
const BASE_FOV = 42;

// portrait → 1, ultra-wide desktop → near 1. >1 means "narrower than reference".
function portraitFactor(aspect: number) {
  return THREE.MathUtils.clamp(REF_ASPECT / Math.max(aspect, 0.35), 1, 2);
}

function CameraRig() {
  const scroll = useScroll();
  const { camera, pointer, size } = useThree();
  const desired = useRef(new THREE.Vector3());
  const target = useRef(new THREE.Vector3());
  const lastFov = useRef(0);

  useFrame((_state, dt) => {
    const o = scroll.offset;
    const orbitT = THREE.MathUtils.smoothstep(o, 0.12, 1.0);

    const aspect = size.width / Math.max(1, size.height);
    // keep horizontal coverage ~constant: as the viewport narrows, open up the
    // vertical FOV (capped so it never fisheyes) and pull back a touch.
    const cam = camera as THREE.PerspectiveCamera;
    // widen FOV just enough that the wide broom still fits on a tall phone, but
    // not so much that it shrinks — the broom is scaled up to match.
    const fov = THREE.MathUtils.clamp(
      THREE.MathUtils.radToDeg(
        2 * Math.atan((Math.tan(THREE.MathUtils.degToRad(BASE_FOV) / 2) * REF_ASPECT) / Math.max(aspect, 0.4)),
      ),
      BASE_FOV,
      60,
    );
    if (Math.abs(fov - lastFov.current) > 0.01) {
      cam.fov = fov;
      cam.updateProjectionMatrix();
      lastFov.current = fov;
    }
    const pull = THREE.MathUtils.clamp(Math.sqrt(REF_ASPECT / Math.max(aspect, 0.4)), 1, 1.12);

    // Hero is dead head-on (az 0); past the hero it sweeps around the broom
    // while keeping the sunset in frame.
    const az = orbitT * 1.2;
    const radius = (9.4 - Math.sin(orbitT * Math.PI) * 2.8) * pull;
    const height = 1.5 + o * 3.4;

    desired.current.set(Math.sin(az) * radius, height, Math.cos(az) * radius);
    // parallax kept tiny during the hero so the headline reads as fixed type
    const par = 0.18 + orbitT * 0.6;
    desired.current.x += pointer.x * par;
    desired.current.y += pointer.y * par * 0.6;

    const k = 1 - Math.pow(0.0016, dt);
    camera.position.lerp(desired.current, k);
    target.current.set(0, 1.15 + o * 0.6, -0.5);
    camera.lookAt(target.current);
  });
  return null;
}

// Broom holder that grows on portrait screens so the 3D stays dominant on phones.
function BroomRig() {
  const grp = useRef<THREE.Group>(null);
  const { size } = useThree();
  const scale = 1 + (portraitFactor(size.width / Math.max(1, size.height)) - 1) * 0.5;
  useFrame(() => {
    if (grp.current) grp.current.scale.setScalar(scale);
  });
  return (
    <group ref={grp} position={[0, 0, 1.1]}>
      <Broom />
    </group>
  );
}

export default function Experience() {
  return (
    <>
      <CameraRig />
      <Sky />
      <Env />

      {/* golden-hour lighting */}
      <hemisphereLight args={["#ffd9b0", "#2a2030", 0.95]} />
      <ambientLight intensity={0.22} color="#ffd9b8" />
      <directionalLight
        position={[SUN_DIR.x * 80, SUN_DIR.y * 80 + 10, SUN_DIR.z * 80]}
        intensity={3.0}
        color="#ffb866"
      />
      <directionalLight position={[5, 4, 9]} intensity={0.8} color="#ffe0b0" />
      <pointLight position={[0, 1.2, 2.4]} intensity={7} distance={10} color="#ffcaa0" />

      <Mountains />
      <Mist />
      {/* Hero is the cinematic scene itself — no 3D wordmark. The broom is the
          subject, scaled up on narrow screens so it stays the hero on mobile. */}
      <BroomRig />
      <Embers />

      <EffectComposer>
        <Bloom
          intensity={0.9}
          luminanceThreshold={0.55}
          luminanceSmoothing={0.25}
          mipmapBlur
        />
        <Vignette offset={0.28} darkness={0.9} eskil={false} />
      </EffectComposer>
    </>
  );
}
