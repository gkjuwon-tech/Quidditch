"""rider_input — turn the rider physically waving the broom into RiderIntent.

Challenge 3: "wave the broom up/down/left/right and it flies that way."
The flight software already has fly-by-intent (nimbus_fc/intent/mapper.py) — it
takes a normalized RiderIntent(pitch, roll, yaw, lift) in [-1, 1] and turns it
into a SAFE, velocity-capped setpoint (centre the stick and it auto-hovers).

So the hardware job is just the *input transducer*: read the handle's own pose
(the rider leans/twists the whole broom) plus a throttle grip, and emit that
RiderIntent. The handle IMU (firmware/pinmap.csv IMU_A) gives lean angles; a
twist grip gives yaw; a thumb throttle (or a vertical heave gesture) gives lift.

    pose ─► RiderInputDecoder ─► RiderIntent ─► IntentMapper ─► setpoint ─► fans
    (lean/twist/throttle)         (this file)     (software, already exists)

    python3 firmware/rider_input.py   # demo: wave it, watch where it commands

Sign convention matches nimbus_fc/core/types.py RiderIntent:
  lean nose-forward (+) -> fly forward,  lean right (+) -> fly right,
  twist right (+)       -> yaw right,    throttle up (+) -> climb.
"""
from __future__ import annotations

import math
import os
import sys

# full-scale gestures: how far you lean/twist to ask for max command
FULL_LEAN_DEG  = 30.0     # lean this much from neutral -> full velocity wish
FULL_TWIST_DPS = 60.0     # twist rate for full yaw wish
DEADBAND       = 0.04     # ignore tiny tremor (rider isn't a robot)
EXPO           = 0.35     # soften centre, keep ends crisp (fine hover control)
HEAVE_G        = 0.6      # vertical hand accel (g) that maps to full climb wish


def _shape(x: float) -> float:
    """Deadband + cubic expo + clamp to [-1, 1]."""
    if abs(x) < DEADBAND:
        return 0.0
    s = (abs(x) - DEADBAND) / (1.0 - DEADBAND)
    s = (1.0 - EXPO) * s + EXPO * s ** 3
    return math.copysign(min(s, 1.0), x)


class RiderInputDecoder:
    """Maps measured handle motion to a normalized RiderIntent.

    Inputs (all from the handle, per tick):
      pitch_deg : nose-forward lean angle, + = lean forward
      roll_deg  : bank angle, + = lean right
      yaw_dps   : twist rate of the grip, + = twist right
      throttle  : thumb throttle, [-1, 1] (+ = up); None to use heave instead
      heave_g   : vertical hand acceleration in g (used only if throttle is None)
    Returns a RiderIntent (the real one if nimbus_fc is importable, else a
    field-compatible stand-in).
    """

    def decode(self, pitch_deg, roll_deg, yaw_dps,
               throttle=None, heave_g=0.0):
        pitch = _shape(pitch_deg / FULL_LEAN_DEG)
        roll = _shape(roll_deg / FULL_LEAN_DEG)
        yaw = _shape(yaw_dps / FULL_TWIST_DPS)
        if throttle is None:
            lift = _shape(heave_g / HEAVE_G)
        else:
            lift = _shape(throttle)
        return make_intent(pitch, roll, yaw, lift)


# ---- use the real RiderIntent if we can find the flight package ---------
def _load_real_intent():
    here = os.path.dirname(os.path.abspath(__file__))
    broom = os.path.normpath(os.path.join(here, "..", "..", "broom"))
    if broom not in sys.path:
        sys.path.insert(0, broom)
    try:
        from nimbus_fc.core.types import RiderIntent  # type: ignore
        return RiderIntent
    except Exception:
        return None


_RIDER_INTENT = _load_real_intent()


def make_intent(pitch, roll, yaw, lift):
    if _RIDER_INTENT is not None:
        return _RIDER_INTENT(pitch, roll, yaw, lift)
    return dict(pitch=pitch, roll=roll, yaw=yaw, lift=lift)


def _fields(intent):
    if isinstance(intent, dict):
        return intent
    return dict(pitch=intent.pitch, roll=intent.roll,
                yaw=intent.yaw, lift=intent.lift)


def _demo():
    dec = RiderInputDecoder()
    print("rider_input — wave the broom, watch the commanded intent\n")
    gestures = [
        ("hold still (hands off)",        0,   0,   0,   0.0),
        ("lean forward hard",            26,   0,   0,   0.0),
        ("lean left + dive forward",     14, -18,   0,  -0.4),
        ("bank right into a turn",        6,  20,  35,   0.0),
        ("pull up and climb",           -10,   0,   0,   0.7),
        ("twist to spin on the spot",     0,   0,  55,   0.0),
    ]
    for name, p, r, y, thr in gestures:
        it = _fields(dec.decode(p, r, y, throttle=thr))
        print(f"  {name:28s} -> pitch{it['pitch']:+.2f} roll{it['roll']:+.2f} "
              f"yaw{it['yaw']:+.2f} lift{it['lift']:+.2f}")

    print("\nbacked by the real intent type:", _RIDER_INTENT is not None)
    _maybe_full_loop(dec)


def _maybe_full_loop(dec):
    """If the flight stack imports, prove the gesture actually moves the broom
    through the REAL intent mapper (velocity-capped, auto-hover on release)."""
    if _RIDER_INTENT is None:
        print("(nimbus_fc not found on path — skipping the closed-loop check)")
        return
    try:
        import numpy as np
        from nimbus_fc.core.params import Params
        from nimbus_fc.core.types import FlightMode, State
        from nimbus_fc.intent.mapper import IntentMapper
    except Exception as e:
        print(f"(closed-loop check skipped: {e})")
        return
    p = Params()
    mapper = IntentMapper(p)
    st = State()
    mapper.reset(st)
    print("\nclosed loop through nimbus_fc.IntentMapper (heading = +x):")
    for name, pd, rd, yd, thr in [
        ("hands off",        0,  0,  0,  0.0),
        ("lean forward",    26,  0,  0,  0.0),
        ("lean right",       0, 26,  0,  0.0),
        ("throttle up",      0,  0,  0,  0.8),
    ]:
        it = dec.decode(pd, rd, yd, throttle=thr)
        sp = mapper.update(it, st, dt=0.01, mode=FlightMode.POSITION)
        v = sp.vel_ff
        print(f"  {name:14s} -> commanded velocity "
              f"[fwd {v[0]:+.1f}, right {-v[1]:+.1f}, up {v[2]:+.1f}] m/s "
              f"(cap {p.max_speed_xy:.0f})")


if __name__ == "__main__":
    _demo()
