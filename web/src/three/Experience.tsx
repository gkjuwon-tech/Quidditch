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
import ExtrudedText from "./ExtrudedText";
import { SUN_DIR } from "./scene";

// Scroll drives the camera. Through the hero (offset < ~0.12) it stays head-on
// so the wordmark never appears to rotate; only a slow dolly-in. Past the hero
// it sweeps ~270° around the broom while dollying and rising with scroll.
// Reference framing is authored for a wide desktop viewport. On narrower /
// portrait screens we widen the (vertical) FOV and dolly the camera back so the
// broom + wordmark keep the SAME composition they have on a PC — the mobile
// view reads like the desktop one instead of cropping into the broom.
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
    // not so much that it shrinks — the broom/wordmark are scaled up to match.
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

    // Hero is dead head-on (az 0) so the wordmark reads as flat, fixed type;
    // past the hero it sweeps around the broom while keeping the sunset in frame.
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

// The big 3D wordmark, sitting well behind the broom so the broom passes
// cleanly in front of it. Fixed orientation (never rotates). It is the hero of
// the scene: a real cast-metal front face that reflects the sunset, scaled up on
// narrow screens, and fading SMOOTHLY out as the page scrolls past the hero
// (no hard pop). The fade is driven through `getOpacity` into every layer.
function Wordmark() {
  const grp = useRef<THREE.Group>(null);
  const scroll = useScroll();
  const { size } = useThree();
  // On a tall phone the wide wordmark would overflow, so scale it DOWN just
  // enough to sit edge-to-edge (still far larger on screen than the old
  // pulled-back framing, and fully readable instead of clipping letters).
  const wordScale = 1 - (portraitFactor(size.width / Math.max(1, size.height)) - 1) * 0.2;
  const fade = () => 1 - THREE.MathUtils.smoothstep(scroll.offset, 0.07, 0.17);

  useFrame(() => {
    if (grp.current) grp.current.scale.setScalar(wordScale);
  });

  return (
    <group ref={grp} position={[0, 1.5, -2.6]}>
      <ExtrudedText
        fontSize={1.7}
        letterSpacing={0.01}
        position={[0, 1.0, 0]}
        front="#eaf1ff"
        side="#39414f"
        getOpacity={fade}
        frontMaterial={
          <meshPhysicalMaterial
            color="#f4f8ff"
            emissive="#dfe8ff"
            emissiveIntensity={0.4}
            metalness={0.35}
            roughness={0.28}
            clearcoat={0.9}
            clearcoatRoughness={0.18}
            envMapIntensity={0.35}
          />
        }
      >
        QUIDDITCH
      </ExtrudedText>
      <ExtrudedText
        fontSize={1.7}
        letterSpacing={0.14}
        position={[0, -1.0, 0]}
        front="#cfd8e2"
        side="#2a2f37"
        getOpacity={fade}
        frontMaterial={
          <meshPhysicalMaterial
            color="#9fb0bf"
            emissive="#33485c"
            emissiveIntensity={0.7}
            metalness={0.55}
            roughness={0.5}
            clearcoat={0.5}
            clearcoatRoughness={0.32}
            envMapIntensity={0.12}
          />
        }
      >
        IS REAL
      </ExtrudedText>
    </group>
  );
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
      <Wordmark />
      {/* broom pushed toward camera so it clearly passes in front of the type;
          scaled up on narrow screens so it stays the hero on mobile. */}
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
