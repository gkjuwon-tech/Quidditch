import { Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import { useProgress } from "@react-three/drei";
import * as THREE from "three";
import Hero3D from "../three/Hero3D";

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
      <div className="loader__pct">기체 워밍업 {Math.round(progress)}%</div>
    </div>
  );
}

export default function Hero() {
  return (
    <section className="hero">
      <div className="hero__canvas">
        <Canvas
          shadows
          dpr={[1, 2]}
          gl={{
            antialias: true,
            toneMapping: THREE.ACESFilmicToneMapping,
            toneMappingExposure: 1.05,
          }}
          camera={{ position: [0, 0.8, 12.5], fov: 40, near: 0.1, far: 260 }}
        >
          <Suspense fallback={null}>
            <Hero3D />
          </Suspense>
        </Canvas>
      </div>

      <div className="hero__vignette" />

      <nav className="nav">
        <div className="nav__brand">
          NIMBUS <span>9¾</span>
        </div>
        <div className="nav__links">
          <a href="#manifesto">선언</a>
          <a href="#balls">공 3종</a>
          <a href="#safety">안전</a>
          <a href="#roadmap">로드맵</a>
          <a className="soon">코덱스</a>
          <a className="soon">엔지니어링</a>
          <a className="soon">후원</a>
        </div>
      </nav>

      <div className="hero__overlay">
        <div className="hero__kicker">CODENAME · NIMBUS-9¾ · PHASE 0</div>
        <p className="hero__sub">
          2001년의 퀴디치는 <b>판타지</b>였습니다.
          <br />
          2026년의 퀴디치는 <b>엔지니어링 프로젝트</b>입니다.
        </p>
        <div className="hero__row">
          <a className="btn" href="#manifesto">
            왜 지금인가 ↓
          </a>
          <a className="btn btn--ghost" href="#balls">
            인사이드아웃 드론볼 보기
          </a>
        </div>
        <p className="hero__note" style={{ marginTop: 20 }}>
          ※ CG 아님. 와이어 아님. 마법 아님. 그냥 충돌회피 알고리즘을 존나 잘 짤 뿐.
        </p>
      </div>

      <div className="scrollcue">
        스크롤
        <i />
      </div>

      <Loader />
    </section>
  );
}
