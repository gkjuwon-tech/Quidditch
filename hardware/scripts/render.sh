#!/usr/bin/env bash
# Render every CAD model to a set of orthographic + iso PNG views (and a
# cutaway that reveals the hidden fans / swarm core). Headless-safe via xvfb.
#   usage: scripts/render.sh [WxH]
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CAD="$HERE/cad"
OUT="$HERE/build/views"
RENDERS="$HERE/renders"
SIZE="${1:-1400x900}"
mkdir -p "$OUT" "$RENDERS"
export OPENSCADPATH="$CAD"

RUN="openscad"
if [ -z "${DISPLAY:-}" ] && command -v xvfb-run >/dev/null 2>&1; then
  RUN="xvfb-run -a openscad"
fi

PARTS=("broom" "snitch" "bludger" "quaffle")
declare -A ISO=(
  [broom]="0,0,0,66,0,210,0"
  [snitch]="0,0,0,62,0,30,0"
  [bludger]="0,0,0,62,0,30,0"
  [quaffle]="0,0,0,62,0,30,0"
)
declare -A SIDE=(
  [broom]="0,0,0,80,0,205,0"
  [snitch]="0,0,0,90,0,0,0"
  [bludger]="0,0,0,90,0,0,0"
  [quaffle]="0,0,0,90,0,0,0"
)

shot() { # file out cam extra
  $RUN -o "$2" --imgsize="${SIZE/x/,}" --autocenter --viewall \
       --projection=p --camera="$3" ${4:-} "$CAD/$1.scad" >/dev/null 2>&1
}

for p in "${PARTS[@]}"; do
  echo "[$p]"
  shot "$p" "$OUT/${p}_iso.png"     "${ISO[$p]}"
  shot "$p" "$OUT/${p}_side.png"    "${SIDE[$p]}"
  shot "$p" "$OUT/${p}_top.png"     "0,0,0,0,0,180,0"
  # cutaway: preview ghosting reveals the internals (fast; no CGAL needed)
  shot "$p" "$OUT/${p}_cutaway.png" "${ISO[$p]}" "-D cutaway=true"
  # publish a hero iso + cutaway into the committed renders/ folder
  cp "$OUT/${p}_iso.png"     "$RENDERS/${p}.png"
  cp "$OUT/${p}_cutaway.png" "$RENDERS/${p}_cutaway.png"
done

echo "views -> $OUT   heroes -> $RENDERS"
