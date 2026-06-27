#!/usr/bin/env python3
"""NIMBUS-9¾ broom -- runnable SITL scenarios.

    python scenarios/run.py            # list scenarios
    python scenarios/run.py hover      # run one
    python scenarios/run.py all        # run them all

Each scenario flies the full flight-control + safety stack against the 6-DOF
plant and prints a terminal report (state timeline + ASCII telemetry). CSVs
are written to scenarios/out/ for plotting (see tools/plot.py).
"""

from __future__ import annotations

import os
import sys

# Make `nimbus_fc` importable when run straight from the repo.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from nimbus_fc.core.types import FlightMode, RiderIntent, State  # noqa: E402
from nimbus_fc.safety.commander import Commands  # noqa: E402
from nimbus_fc.sim.rider import RiderScript, Segment  # noqa: E402
from nimbus_fc.sim.simulator import Simulator  # noqa: E402
from nimbus_fc.sim.wind import Wind  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")

# Control backend for all scenarios: "python" (default) or "rust". Set by CLI.
_BACKEND = "python"


def _mk(**kw) -> Simulator:
    return Simulator(backend=_BACKEND, **kw)


# Reporting
def report(name: str, blurb: str, sim: Simulator) -> None:
    rows = sim.log.rows
    print("\n" + "=" * 74)
    print(f"  SCENARIO: {name}")
    print(f"  {blurb}")
    print("=" * 74)

    # State-transition timeline
    print("  flight log:")
    last = None
    for r in rows:
        if r["state"] != last:
            print(f"    t={r['t']:6.2f}s  ->  {r['state']:<18} "
                  f"@ ({r['x']:6.1f},{r['y']:6.1f},{r['z']:5.1f}) m, "
                  f"{r['soc']:4.0f}% batt")
            last = r["state"]
    f = rows[-1]
    print(f"  final: {f['state']} at ({f['x']:.1f},{f['y']:.1f},{f['z']:.1f}) m, "
          f"battery {f['soc']:.0f}%")

    # Telemetry sparklines
    print("  telemetry:")
    for line in sim.log.summary(["z", "speed", "pitch", "soc"]).splitlines():
        print("    " + line)

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f"{name}.csv")
    sim.log.to_csv(path)
    print(f"  csv: {os.path.relpath(path)}")


def _ground(x=0.0, y=0.0):
    return State(pos=np.array([x, y, 0.0]))


def _launch(*extra):
    return RiderScript([
        Segment(0.0, cmd=Commands(arm=True)),
        Segment(0.5, cmd=Commands(takeoff=True)),
        *extra,
    ])


# Scenarios
def scn_hover():
    sim = _mk(initial=_ground())
    script = _launch(Segment(8.0, intent=RiderIntent()))
    sim.run(18.0, lambda t, s: script(t))
    report("hover", "Arm, auto-takeoff, then let go of the sticks. The broom "
                    "holds position.", sim)


def scn_joyride():
    sim = _mk(initial=_ground())
    # Fly a rough rectangle using only stick deflections, then release to hold.
    script = _launch(
        Segment(7.0, intent=RiderIntent(pitch=0.7)),
        Segment(12.0, intent=RiderIntent(roll=0.7)),
        Segment(17.0, intent=RiderIntent(pitch=-0.7)),
        Segment(22.0, intent=RiderIntent(roll=-0.7)),
        Segment(27.0, intent=RiderIntent(yaw=0.6, lift=0.5)),
        Segment(31.0, intent=RiderIntent()),
    )
    sim.run(40.0, lambda t, s: script(t))
    report("joyride", "Hand-flown box pattern on stick velocity commands, "
                      "climb + yaw, then released to a stable hover.", sim)


def scn_geofence():
    sim = _mk(initial=_ground())
    script = _launch(
        Segment(8.0, intent=RiderIntent(pitch=1.0, roll=1.0)),    # corner
        Segment(40.0, intent=RiderIntent(pitch=-1.0, roll=-1.0)),  # opposite
        Segment(70.0, intent=RiderIntent(lift=1.0)),              # ceiling
    )
    sim.run(85.0, lambda t, s: script(t))
    xs = [r["x"] for r in sim.log.rows]
    ys = [r["y"] for r in sim.log.rows]
    zs = [r["z"] for r in sim.log.rows]
    report("geofence", "Rider SLAMS the sticks into every wall and the ceiling. "
                       "The invisible rubber walls hold.", sim)
    print(f"  containment: x in [{min(xs):.1f},{max(xs):.1f}] (wall +-50), "
          f"y in [{min(ys):.1f},{max(ys):.1f}] (wall +-25), "
          f"z_max={max(zs):.1f} (ceiling 18)")


def scn_battery():
    sim = _mk(initial=_ground(20.0, 10.0), initial_soc=0.33)
    # Fly away from the pit; battery crosses the RTP threshold mid-flight.
    script = _launch(Segment(7.0, intent=RiderIntent(pitch=0.6, roll=-0.3)))
    sim.run(70.0, lambda t, s: script(t))
    report("battery", "Battery sags below the Return-To-Pit threshold mid-joyride. "
                      "The broom overrides the rider, flies home, and lands.", sim)


def scn_killswitch():
    sim = _mk(initial=_ground())
    script = _launch(
        Segment(8.0, intent=RiderIntent(pitch=0.5)),
        Segment(13.0, cmd=Commands(kill=True)),   # emergency-stop input
    )
    sim.run(28.0, lambda t, s: script(t))
    after = [r for r in sim.log.rows if r["t"] > 13.2]
    vmax = max(-r["vz"] for r in after) if after else 0.0
    report("killswitch", "The emergency stop is pressed at speed. It is NOT a "
                         "motor cut -- it is a gentle, controlled descent.", sim)
    print(f"  peak descent rate after KILL: {vmax:.2f} m/s (gentle by design)")


def scn_estimate():
    sim = _mk(initial=_ground(-30.0, 0.0), state_source="estimate", seed=2)
    script = _launch(
        Segment(7.0, intent=RiderIntent(pitch=0.5, roll=0.3)),
        Segment(16.0, intent=RiderIntent()),
    )
    sim.run(28.0, lambda t, s: script(t))
    report("estimate", "Same broom, but flying on the onboard estimate from "
                       "NOISY IMU + GNSS (no ground truth). Mahony + INS fusion.", sim)


def scn_wind():
    wind = Wind(steady=(8.0, -4.0, 0.0), gust_sigma=2.0, gust_tau=1.5, seed=3)
    sim = _mk(initial=_ground(), wind=wind)
    script = _launch(Segment(8.0, intent=RiderIntent()))
    sim.run(40.0, lambda t, s: script(t))
    tail = [r for r in sim.log.rows if r["t"] > 30]
    off = np.hypot(np.mean([r["x"] for r in tail]), np.mean([r["y"] for r in tail]))
    report("wind", "Hands-off hover in a steady ~9 m/s wind with 2 m/s gusts. "
                   "The velocity integrator quietly cancels the drift.", sim)
    print(f"  hands-off hold against the wind: {off:.2f} m offset, "
          f"tilt held ~{max(abs(r['pitch']) for r in tail):.1f} deg")


def scn_ekf_wind():
    wind = Wind(steady=(6.0, -3.0, 0.0), gust_sigma=1.5, gust_tau=1.5, seed=2)
    sim = _mk(initial=_ground(-30.0, 0.0), state_source="estimate",
              estimator="ekf", wind=wind, seed=2)
    script = _launch(
        Segment(7.0, intent=RiderIntent(pitch=0.5, roll=0.3)),
        Segment(16.0, intent=RiderIntent()),
    )
    sim.run(28.0, lambda t, s: script(t))
    t, e = sim.dyn.state, sim.estimator
    from nimbus_fc.core import math3d as _m
    ae = np.rad2deg(np.linalg.norm(_m.quat_error_angle_axis(t.quat, e.q)))
    report("ekf-wind", "Flying on the 15-state EKF (noisy IMU+GNSS+mag) in "
                       "gusting wind -- no ground truth anywhere.", sim)
    print(f"  estimator vs truth at landing: attitude err {ae:.2f} deg, "
          f"position err {np.linalg.norm(t.pos - e.pos):.3f} m")


SCENARIOS = {
    "hover": scn_hover,
    "joyride": scn_joyride,
    "geofence": scn_geofence,
    "battery": scn_battery,
    "killswitch": scn_killswitch,
    "wind": scn_wind,
    "estimate": scn_estimate,
    "ekf-wind": scn_ekf_wind,
}


def main(argv: list[str]) -> int:
    global _BACKEND
    argv = list(argv)
    if "--backend" in argv:
        i = argv.index("--backend")
        _BACKEND = argv[i + 1]
        del argv[i:i + 2]
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        print("  scenarios:", ", ".join(SCENARIOS), "| all")
        print("  --backend python|rust   (rust = compiled real-time core)")
        return 0
    name = argv[0]
    if name == "all":
        for fn in SCENARIOS.values():
            fn()
        return 0
    if name not in SCENARIOS:
        print(f"unknown scenario '{name}'. choose from: "
              f"{', '.join(SCENARIOS)}, all")
        return 1
    SCENARIOS[name]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
