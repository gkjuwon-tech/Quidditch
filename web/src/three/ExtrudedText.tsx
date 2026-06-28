import { useMemo, useRef, type ReactNode } from "react";
import { Text } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

// Pseudo-extruded headline: the glyphs are stacked in many thin layers along
// -Z so the wordmark reads as a solid block of type with real depth. The front
// face (i=0) can take a real PBR material (passed via `frontMaterial`) so it
// catches the sunset environment and reads as cast metal — the deeper layers
// stay cheap flat colour to fake the extruded sides. The parent group controls
// orientation, so it never billboards/rotates on its own.
export default function ExtrudedText({
  children,
  position = [0, 0, 0],
  fontSize = 1,
  letterSpacing = 0,
  depth = 0.34,
  layers = 18,
  front = "#f6efe2",
  side = "#4a2a10",
  font = "/fonts/Anton.ttf",
  frontMaterial,
  getOpacity,
}: {
  children: string;
  position?: [number, number, number];
  fontSize?: number;
  letterSpacing?: number;
  depth?: number;
  layers?: number;
  front?: string;
  side?: string;
  font?: string;
  frontMaterial?: ReactNode;
  getOpacity?: () => number;
}) {
  const shades = useMemo(() => {
    const f = new THREE.Color(front);
    const s = new THREE.Color(side);
    return Array.from({ length: layers }, (_, i) => {
      const t = layers === 1 ? 0 : i / (layers - 1);
      return "#" + f.clone().lerp(s, Math.pow(t, 0.7)).getHexString();
    });
  }, [front, side, layers]);

  const step = layers === 1 ? 0 : depth / (layers - 1);
  const meshes = useRef<(THREE.Mesh | null)[]>([]);
  const applied = useRef(false);

  // Smooth opacity fade driven by the parent (scroll). Mutating material.opacity
  // per frame is cheap and, crucially, avoids troika text re-layout (no .sync()).
  useFrame(() => {
    if (!getOpacity) return;
    const o = THREE.MathUtils.clamp(getOpacity(), 0, 1);
    for (const m of meshes.current) {
      if (!m) continue;
      const mat = m.material as THREE.Material;
      if (!applied.current) {
        mat.transparent = true;
        mat.depthWrite = true;
        mat.needsUpdate = true;
      }
      mat.opacity = o;
      m.visible = o > 0.01;
    }
    applied.current = true;
  });

  return (
    <group position={position}>
      {shades.map((c, i) => (
        <Text
          key={i}
          ref={(m) => (meshes.current[i] = m as unknown as THREE.Mesh | null)}
          font={font}
          fontSize={fontSize}
          anchorX="center"
          anchorY="middle"
          letterSpacing={letterSpacing}
          // i=0 is the bright front face at z≈0; deeper layers go back and dark
          position={[0, i * step * 0.1, -i * step]}
          color={c}
          outlineWidth={i === 0 ? fontSize * 0.006 : 0}
          outlineColor="#160b05"
          outlineOpacity={0.55}
        >
          {children}
          {i === 0 ? frontMaterial : null}
        </Text>
      ))}
    </group>
  );
}
