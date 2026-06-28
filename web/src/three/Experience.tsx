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
    const fov = THREE.MathUtils.clamp(
      THREE.MathUtils.radToDeg(
        2 * Math.atan((Math.tan(THREE.MathUtils.degToRad(BASE_FOV) / 2) * REF_ASPECT) / Math.max(aspect, 0.4)),
      ),
      BASE_FOV,
      74,
    );
    if (Math.abs(fov - lastFov.current) > 0.01) {
      cam.fov = fov;
      cam.updateProjectionMatrix();
      lastFov.current = fov;
    }
    const pull = THREE.MathUtils.clamp(Math.sqrt(REF_ASPECT / Math.max(aspect, 0.4)), 1, 1.7);

    // gentle sway that keeps the camera on the sun-facing side, so the sunset
    // sky and the back-lit, rim-lit ridgeline stay in frame the whole way down
    // (orbiting all the way round would swing into the dark anti-sun side).
    const az = -0.22 + orbitT * 1.15;
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
// cleanly in front of it. Fixed orientation (never rotates); fades on scroll-in.
function Wordmark() {
  const grp = useRef<THREE.Group>(null);
  const scroll = useScroll();
  useFrame(() => {
    if (grp.current) grp.current.visible = scroll.offset < 0.11;
  });
  return (
    <group ref={grp} position={[0, 1.45, -2.6]}>
      <ExtrudedText
        fontSize={1.55}
        letterSpacing={0.01}
        position={[0, 0.92, 0]}
        front="#f7f0e3"
        side="#5a3414"
      >
        QUIDDITCH
      </ExtrudedText>
      <ExtrudedText
        fontSize={1.55}
        letterSpacing={0.14}
        position={[0, -0.9, 0]}
        front="#ffb657"
        side="#6e3409"
      >
        IS REAL
      </ExtrudedText>
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
      {/* broom pushed toward camera so it clearly passes in front of the type */}
      <group position={[0, 0, 1.1]}>
        <Broom />
      </group>
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
