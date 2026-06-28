# 3D 에셋 출처 & 라이선스

이 페이지의 3D 에셋은 전부 **외부에서 검증된 무료(CC0 / OFL) 고품질 에셋**입니다.
직접 손으로 만든 모델·셰이더·HDRI는 없습니다 (요구사항).

## 모델 (glTF → 압축 후 .glb)

| 파일 | 원본 | 출처 | 라이선스 |
|------|------|------|----------|
| `models/plastic_broom.glb` | Plastic Broom | [Poly Haven](https://polyhaven.com/a/plastic_broom) | CC0 |
| `models/mountainside.glb` | Mountainside | [Poly Haven](https://polyhaven.com/a/mountainside) | CC0 |
| `models/coastal_cliff_02.glb` | Coastal Cliff 02 | [Poly Haven](https://polyhaven.com/a/coastal_cliff_02) | CC0 |

> 원본은 glTF + .bin + 텍스처 번들. `@gltf-transform`으로 텍스처를 WebP로
> 재압축하고 단일 `.glb`로 패킹해 용량을 1/10 수준으로 줄였습니다.

## HDRI 환경광

| 파일 | 원본 | 출처 | 라이선스 |
|------|------|------|----------|
| `hdri/sky_mountain_2k.hdr` | Drakensberg Solitary Mountain (Pure Sky) | [Poly Haven](https://polyhaven.com/a/drakensberg_solitary_mountain_puresky) | CC0 |

## GLSL 셰이더

| 위치 | 내용 | 출처 | 라이선스 |
|------|------|------|----------|
| `src/three/glsl.ts` | 3D Simplex Noise (`snoise`) | [ashima/webgl-noise](https://github.com/ashima/webgl-noise) — Ian McEwan, Ashima Arts; Stefan Gustavson | MIT / public domain |

> 대기(안개)·엠버 파티클 셰이더는 위 검증된 noise 함수를 토대로 구성했습니다.

## 폰트

| 파일 | 폰트 | 라이선스 |
|------|------|----------|
| `fonts/Cinzel.ttf` | Cinzel (Google Fonts) | OFL |
| `fonts/SpaceGrotesk.ttf` | Space Grotesk (Google Fonts) | OFL |
