import { Suspense, useEffect, useRef, type MutableRefObject } from "react";
import { Canvas } from "@react-three/fiber";
import { ScrollControls, Scroll, useScroll, useProgress } from "@react-three/drei";
import * as THREE from "three";
import Experience from "./three/Experience";
import Sections from "./components/Sections";
import { FOG_COLOR } from "./three/scene";

const PAGES = 6.2;

const NAV = [
  { label: "Manifesto", id: "manifesto" },
  { label: "Balls", id: "balls" },
  { label: "Safety", id: "safety" },
  { label: "Roadmap", id: "roadmap" },
];

function Loader() {
  const { progress, active } = useProgress();
  return (
    <div className="loader" style={{ opacity: active ? 1 : 0, pointerEvents: active ? "auto" : "none" }}>
      <div className="loader__brand">
        NIMBUS <span>9¾</span>
      </div>
      <div className="loader__bar">
        <i style={{ width: `${progress}%` }} />
      </div>
      <div className="loader__pct">Warming up the engine · {Math.round(progress)}%</div>
    </div>
  );
}

function ScrollCapture({ elRef }: { elRef: MutableRefObject<HTMLElement | null> }) {
  const scroll = useScroll();
  useEffect(() => {
    elRef.current = scroll.el;
  }, [scroll, elRef]);
  return null;
}

export default function App() {
  const scrollElRef = useRef<HTMLElement | null>(null);

  const goTo = (id: string) => {
    const el = scrollElRef.current;
    const sec = document.getElementById(id);
    if (!el || !sec) return;
    el.scrollTo({ top: el.scrollTop + sec.getBoundingClientRect().top, behavior: "smooth" });
  };

  return (
    <main className="stage">
      <Canvas
        dpr={[1, 1.8]}
        gl={{
          antialias: true,
          toneMapping: THREE.ACESFilmicToneMapping,
          toneMappingExposure: 1.15,
        }}
        camera={{ position: [-2.42, 1.45, 9.1], fov: 42, near: 0.1, far: 2000 }}
      >
        <color attach="background" args={["#21161d"]} />
        <fog attach="fog" args={[FOG_COLOR.getHex(), 110, 900]} />
        <Suspense fallback={null}>
          <ScrollControls pages={PAGES} damping={0.3}>
            <ScrollCapture elRef={scrollElRef} />
            <Experience />
            <Scroll html style={{ width: "100%" }}>
              <Sections />
            </Scroll>
          </ScrollControls>
        </Suspense>
      </Canvas>

      <nav className="nav">
        <button className="nav__brand" onClick={() => goTo("top")}>
          NIMBUS <span>9¾</span>
        </button>
        <div className="nav__links">
          {NAV.map((n) => (
            <button key={n.id} onClick={() => goTo(n.id)}>
              {n.label}
            </button>
          ))}
          <span className="soon">Codex</span>
          <span className="soon">Engineering</span>
          <span className="soon">Sponsorship</span>
        </div>
      </nav>

      <Loader />
    </main>
  );
}
