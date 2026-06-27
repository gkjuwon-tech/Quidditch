// The Codex page exhibits our ACTUAL source (no GitHub embed). These are
// build-time snapshots of the real files in the repo, kept in ./sources so the
// production bundle is self-contained. Each `path` points at its tree origin.
import snitchPy from "./sources/snitch.py?raw";
import paramsPy from "./sources/params.py?raw";
import mapperPy from "./sources/mapper.py?raw";
import geofencePy from "./sources/geofence.py?raw";
import dementorPy from "./sources/dementor.py?raw";
import fcPy from "./sources/fc.py?raw";
import controlRs from "./sources/control.rs?raw";
import snitchEndurance from "./sources/snitch_endurance.py?raw";
import enduranceMatch from "./sources/endurance_match.py?raw";
import snitchScad from "./sources/snitch.scad?raw";

export type CodeFile = {
  id: string;
  path: string;
  title: string;
  blurb: string;
  lang: "python" | "rust" | "cpp";
  source: string;
};

export type CodeGroup = {
  id: string;
  label: string;
  icon: string;
  files: CodeFile[];
};

export const groups: CodeGroup[] = [
  {
    id: "balls",
    label: "Balls — autonomous swarm",
    icon: "◍",
    files: [
      {
        id: "snitch",
        path: "broom/nimbus_fc/ball/snitch.py",
        title: "Golden Snitch evasion policy",
        blurb: "Predicts a pursuer's future position and breaks the opposite way, mixing figure-eights, dives, and feints to resist being learned.",
        lang: "python",
        source: snitchPy,
      },
      {
        id: "params",
        path: "broom/nimbus_fc/ball/params.py",
        title: "Ball parameters",
        blurb: "Tunable parameters for each ball, including the fatigue_tau speed-decay constant used by the snitch model.",
        lang: "python",
        source: paramsPy,
      },
    ],
  },
  {
    id: "fc",
    label: "Flight control — fly-by-intent",
    icon: "✦",
    files: [
      {
        id: "mapper",
        path: "broom/nimbus_fc/intent/mapper.py",
        title: "Intent mapper",
        blurb: "The pilot does not steer. They supply intent, and the flight computer performs the flying.",
        lang: "python",
        source: mapperPy,
      },
      {
        id: "fc",
        path: "broom/nimbus_fc/fc.py",
        title: "Flight-control cascade",
        blurb: "POSITION → ATTITUDE → RATE → MIXER. A textbook autopilot tuned for a heavy, manned broom.",
        lang: "python",
        source: fcPy,
      },
    ],
  },
  {
    id: "safety",
    label: "Safety — fail-safe",
    icon: "◆",
    files: [
      {
        id: "geofence",
        path: "broom/nimbus_fc/safety/geofence.py",
        title: "Geofence (soft walls)",
        blurb: "Craft cannot leave the pitch. Invisible soft walls smoothly repel them at the boundary.",
        lang: "python",
        source: geofencePy,
      },
      {
        id: "dementor",
        path: "broom/nimbus_fc/match/dementor.py",
        title: "Dementor — central monitoring server",
        blurb: "Tracks every craft hundreds of times per second and issues an avoidance command within 0.05 s of a predicted collision.",
        lang: "python",
        source: dementorPy,
      },
    ],
  },
  {
    id: "core",
    label: "Core — Rust",
    icon: "⌬",
    files: [
      {
        id: "control",
        path: "broom/rust/nimbus_core/src/control.rs",
        title: "Control core (Rust)",
        blurb: "The numerical core flashed to real craft, bit-for-bit parity-checked against the Python backend.",
        lang: "rust",
        source: controlRs,
      },
    ],
  },
  {
    id: "hw",
    label: "Hardware — energy & CAD",
    icon: "⬢",
    files: [
      {
        id: "snitch-endurance",
        path: "hardware/analysis/snitch_endurance.py",
        title: "Snitch beamed-power endurance",
        blurb: "A 50 g sphere cannot carry fuel, so it receives 5.8 GHz power from the pitch — enough for a full match.",
        lang: "python",
        source: snitchEndurance,
      },
      {
        id: "endurance-match",
        path: "hardware/analysis/endurance_match.py",
        title: "Broom series-hybrid endurance",
        blurb: "A micro-turbine generator on SAF supplies average power while the battery handles peaks — 25.7 minutes per match.",
        lang: "python",
        source: enduranceMatch,
      },
      {
        id: "snitch-scad",
        path: "hardware/cad/snitch.scad",
        title: "Snitch parametric CAD",
        blurb: "The exterior is unchanged; enabling the cutaway reveals the rectenna liner, supercapacitor ring, and PMIC.",
        lang: "cpp",
        source: snitchScad,
      },
    ],
  },
];

export const allFiles: CodeFile[] = groups.flatMap((g) => g.files);

export const stats = {
  files: allFiles.length,
  lines: allFiles.reduce((n, f) => n + f.source.split("\n").length, 0),
};
