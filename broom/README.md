# 🧹 NIMBUS-9¾ — Broom Flight Control Stack (SITL)

> The flight software for a **manned eVTOL broomstick**. No hardware. No money.
> Just `python` and a 6-DOF physics sim where a 120 kg broom **takes off, holds
> a hover hands-off, bounces off invisible walls, flies itself home on a low
> battery, and settles down softly when you hit the panic button** — all driven
> by the same control + safety stack you'd flash onto the real airframe.

This is **Phase 1** of the [Real Quidditch project](../QUIDDITCH_REALITY_PROJECT.md):
prove the brain in software first, because that's the part you can build for the
price of electricity.

```
$ python scenarios/run.py hover
  t=  0.00s  ->  ARMED      @ (0.0, 0.0, 0.0) m, 100% batt
  t=  0.50s  ->  TAKEOFF    @ (0.0, 0.0, 1.1) m
  t=  1.89s  ->  FLYING     @ (0.0, 0.0, 5.5) m   <- rider lets go; it just hangs there
            z [0.00 .. 5.65] ▁▂▄▅▆▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇
        speed [0.00 .. 4.30] ▁▅▆▇▇▅▃▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
```

---

## Why this exists

A human cannot hand-fly a 3-axis aircraft in a contact sport and live. So the
rider never actually flies the broom — they express **intent**, and the
computer flies. The whole design goal is one sentence:

> **It must be impossible to crash by being bad at flying.**

Everything below is in service of that.

---

## Run it

```bash
pip install numpy                 # the only required dependency
python scenarios/run.py           # list scenarios
python scenarios/run.py hover     # arm, auto-takeoff, hands-off hover
python scenarios/run.py joyride   # hand-flown box pattern on stick velocity
python scenarios/run.py geofence  # SLAM the sticks into every wall -> contained
python scenarios/run.py battery   # low battery -> auto Return-To-Pit + land
python scenarios/run.py killswitch# panic button -> gentle descent, not a drop
python scenarios/run.py estimate  # fly on NOISY IMU+GNSS, no ground truth
python scenarios/run.py all

# tests (16): pip install pytest && python -m pytest
# plots (optional): pip install matplotlib && python tools/plot.py out/battery.csv
```

No hardware, no config, no cloud. Clone and run.

---

## Architecture

A textbook autopilot cascade, benchmarked against the open-source giants and
specialized for a heavy, tilt-to-translate broom:

```
 rider intent ─┐
               ├─►  COMMANDER  ─►  nav setpoint  (or "manual")
 failsafes ────┘   (state machine)      │
                                        ▼
                     manual?  ─►  INTENT MAPPER   (fly-by-intent)
                                        │
                                        ▼
                                   GEOFENCE        (clamp + rubber walls)
                                        │
                                        ▼
        POSITION ─► ATTITUDE ─► RATE ─► MIXER ─► 8 ducted-fan thrusts
        (P→vel PID)  (quat P)   (PID)   (alloc)        │
                                                       ▼
                                              6-DOF RIGID-BODY PLANT
                                              (+ battery, + noisy sensors)
```

| Layer | What it does | Benchmarked against |
|-------|--------------|---------------------|
| **Rate** | body-rate → torque, PID on the gyro | Betaflight inner loop |
| **Attitude** | quaternion error → rate setpoint | PX4 `mc_att_control` |
| **Position** | pos→vel→accel cascade, stopping-distance velocity profile, hard tilt limit | PX4 `mc_pos_control` |
| **Mixer** | wrench → per-fan thrust, saturation that protects torque over collective | Betaflight airmode |
| **Commander** | arm/takeoff/fly/RTP/land/estop state machine | PX4 commander |
| **Geofence** | per-axis position-hold backstop; can't leave the box | ArduPilot fence |
| **Failsafe** | two-stage battery + datalink-loss policy | ArduPilot failsafe |
| **Estimator** | Mahony attitude + alpha-beta GNSS/INS fusion | Crazyflie / PX4 `Q` |

### Our own touches
- **Fly-by-intent.** Sticks centered ⇒ latch & **hold** position, altitude and
  heading — let go and the broom parks in mid-air. Deflect a stick ⇒ command a
  **velocity** (capped to the flight envelope), never a raw tilt. Push twice as
  hard and you don't go twice as crazy; you ask for at most max-speed.
- **The kill switch is a *gentle controlled descent*, not a motor cut.**
  Cutting power on a manned vehicle turns a software fault into a funeral. The
  estop makes the broom sink softly and park itself on the ground (measured
  peak descent ≈ 1.4 m/s).
- **Geofence as a position backstop.** Because the held target sits *inside* the
  wall, any overshoot is actively pulled back — the broom *physically cannot*
  park outside the pitch, no matter how hard the rider slams the sticks.
- **Maneuver-compensated attitude estimator.** The gravity reference is
  corrected by the kinematic acceleration, so hard turns don't corrupt attitude
  the way a naive complementary filter would.

---

## What the sim shows (real numbers)

| Scenario | Result |
|----------|--------|
| Hover hold | hands-off drift < 0.05 m over 10 s |
| Step/diagonal moves | settle in ~3 s, no overshoot-into-flip, tilt ≤ envelope |
| Geofence wall-slam | full-stick into every wall+corner+ceiling → stays inside ±50/±25/18 m |
| Kill switch | from cruise → soft descent (≤ ~1.4 m/s) → landed & disarmed |
| Battery RTP | crosses Return-To-Pit threshold → flies home across the pitch → lands at pit |
| Fly-on-estimate | controller on noisy IMU+GNSS still hovers & maneuvers (looser than truth) |

The vehicle model: 120 kg (rider + airframe), 8 ducted fans on short outriggers
along a 2.4 m body, T/W ≈ 2.4, low roll inertia / high pitch+yaw inertia (it's a
stick). Controllers are tuned in SITL — see the gain notes in
`nimbus_fc/core/params.py`.

---

## Layout

```
nimbus_fc/
  core/         math3d (quaternions, ENU), types, params  (all tunables in one place)
  control/      pid, rate, attitude, position, mixer
  intent/       fly-by-intent mapper
  safety/       commander (state machine), geofence, failsafe
  estimation/   Mahony + alpha-beta estimator
  sim/          6-DOF dynamics, ducted-fan model, battery, sensors, simulator, scripted rider
  telemetry/    logger + ASCII sparklines
  fc.py         the FlightController that wires it all together
scenarios/      runnable demos (this is the showreel)
tests/          16 tests: math, allocation, closed-loop, estimator, safety
tools/          optional matplotlib plotting
```

---

## Honest limitations (engineering, not marketing)

- **Default scenarios fly on ground-truth state** (`state_source="truth"`) —
  standard SITL practice to isolate guidance/control/safety. The `estimate`
  mode runs the full noisy-sensor → estimator → controller chain; it flies, but
  the simple complementary filter is looser than truth and an EKF is the obvious
  next step.
- Aerodynamics are a simple quadratic-drag model; no wind/gust spectrum yet.
- The geofence specializes to a rectangular pitch (the actual pitch shape).
- This is a control/safety SITL, **not** a certified autopilot. It's the brain,
  proven cheaply, so the airframe money has something to land on.

---

*NIMBUS-9¾ v0.1 — "Magic? No. We just wrote the collision-avoidance really well."*
