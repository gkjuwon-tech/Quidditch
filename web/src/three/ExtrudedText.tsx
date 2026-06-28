import { useMemo } from "react";
import { Text } from "@react-three/drei";
import * as THREE from "three";

// Pseudo-extruded headline: the glyphs are stacked in many thin layers along
// -Z so the wordmark reads as a solid block of type with real depth, while the
// front face stays crisp and bright. The parent group controls orientation, so
// it never billboards/rotates on its own. (troika <Text> can't extrude real
// geometry, so we fake it with shaded layers — clean while the camera stays
// roughly head-on, which is exactly when the wordmark is visible.)
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

  return (
    <group position={position}>
      {shades.map((c, i) => (
        <Text
          key={i}
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
        </Text>
      ))}
    </group>
  );
}
