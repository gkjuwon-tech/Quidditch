# 🧹 NIMBUS-9¾ — Broom Flight Control Stack (SITL)

> The flight software for a **manned eVTOL broomstick**. No hardware. No money.
> Just `python` and a 6-DOF physics sim where a 120 kg broom **takes off, holds
> a hover hands-off, bounces off invisible walls, flies itself home on a low
> battery, and settles down softly when you hit the panic button** — all driven
> by the same control + safety stack you'd flash onto the real airframe.

This is **Phase 1** of the [Real Quidditch project](../QUIDDITCH_REALITY_PROJECT.md):
prove the brain in software first, because that's the part you can build for the
price of electricity.

> 🧹 This doc is the **broom** (manned eVTOL flight control). The autonomous
> **balls** — Quaffle, Bludger, Golden Snitch, and the "a ball never hits a
> person" guarantee — are in **[BALLS.md](BALLS.md)** (`python scenarios/balls.py match`).
> The full refereed match (real broom-flown players + the Dementor) is in
> **[MATCH.md](MATCH.md)** (`python scenarios/match.py seek`).

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

## Polyglot: Python brain, Rust reflexes

Python is perfect for the *policy* — the commander, the geofence, the intent
mapping, the whole simulation harness. It is **not** safe for the hard-real-time
inner loop: at 400 Hz you have a **2500 µs** budget per tick, and one garbage-
collection pause or interpreter hiccup blows the deadline. On a manned vehicle
a blown deadline is a destabilized loop is a person falling.

So the hot path — `position → attitude → rate → mixer` — is ported to a
**Rust** core (`rust/nimbus_core`; deterministic, allocation-free on the hot
path, `panic=abort`, `no_std`-capable, one tiny dep: `libm`). It builds as a
cdylib for the host and a staticlib for an MCU, and is called from Python
through `ctypes`. The backend is a one-word switch:

```python
Simulator(backend="rust")     # compiled real-time core
Simulator(backend="python")   # readable reference
```

```bash
make rust            # cargo build --release  -> libnimbus_core.so
make bench           # Python vs Rust latency/jitter
python scenarios/run.py geofence --backend rust
```

**The port is provably behaviour-preserving.** Flying an identical 28 s,
11,200-tick scenario on both backends, the trajectories match to **~1e-13**
(floating-point noise). Same flight, same safety — just real-time-capable.

### It runs on a real flight MCU

The exact same core is `no_std` and cross-compiles to **`thumbv7em-none-eabihf`
(Cortex-M4F)** — the microcontroller class real flight controllers use:

```bash
make embedded   # -> libnimbus_core.a  (ARM EABI, link into firmware)
```

The control core is **~13 KB of `.text`, with 0 bytes of `.data`/`.bss`** — no
heap, no static allocation. On no_std it drops the heap `nc_create` and exposes
a placement-init API (`nc_size`/`nc_init`) so firmware owns the memory. The host
`.so` and the MCU `.a` are built from one source of truth — develop and tune in
Python-driven SITL, flash the identical code.

### Measured control-tick latency (200k iters, budget = 2500 µs @ 400 Hz)

| backend | mean | median | p99.9 | **worst case** | speedup (worst) |
|---------|-----:|-------:|------:|---------------:|----------------:|
| Python  | 125 µs | 64 µs | 516 µs | **2214 µs** | — |
| Rust    | 12 µs | 11 µs | 69 µs | **158 µs** | **~14×** |

Python's worst case (2214 µs) is **88 % of the entire real-time budget** —
one bad GC pause from a missed deadline. Rust's worst case (158 µs) leaves
**94 % headroom**. *That* is why the safety loop is compiled. (Numbers from
`tools/bench.py`; your hardware will vary, the gap won't.)

---

## What the sim shows (real numbers)

| Scenario | Result |
|----------|--------|
| Hover hold | hands-off drift < 0.05 m over 10 s |
| Step/diagonal moves | settle in ~3 s, no overshoot-into-flip, tilt ≤ envelope |
| Geofence wall-slam | full-stick into every wall+corner+ceiling → stays inside ±50/±25/18 m |
| Kill switch | from cruise → soft descent (≤ ~1.4 m/s) → landed & disarmed |
| Battery RTP | crosses Return-To-Pit threshold → flies home, stops over pit, lands within ~1 m |
| Wind hold | hands-off in ~9 m/s wind + 2 m/s gusts → holds within ~0.3 m |
| Fly-on-estimate (EKF) | on noisy IMU+GNSS+mag, in gusting wind: attitude ~1–3°, position ~3–5 cm, 10/10 seeds |

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
  estimation/   15-state error-state EKF (eskf) + complementary filter (legacy)
  sim/          6-DOF dynamics, ducted-fan model, battery, wind/gusts, sensors, simulator
  telemetry/    logger + ASCII sparklines
  control/backend.py   swappable Python / Rust(ctypes) inner-loop backends
  fc.py         the FlightController that wires it all together
rust/nimbus_core/   hard-real-time control core (Rust, C ABI, no deps; host .so + MCU .a)
scenarios/      runnable demos (this is the showreel)  [--backend python|rust]
tests/          21 tests: math, allocation, closed-loop, EKF, safety, backend parity
tools/          bench.py (latency/jitter), plot.py (optional matplotlib)
```

---

## Honest limitations (engineering, not marketing)

- **Default scenarios fly on ground-truth state** (`state_source="truth"`) —
  standard SITL practice to isolate guidance/control/safety. `state_source=
  "estimate"` runs the full noisy-sensor → 15-state EKF → controller chain and
  flies through gusting wind (attitude ~1–3°); the one place it still wanders is
  the most aggressive full-envelope maneuver on an unlucky noise seed.
- Aerodynamics are quadratic drag + a steady-wind/OU-gust model — not a full
  Dryden spectrum or rotor aero.
- The geofence specializes to a rectangular pitch (the actual pitch shape).
- This is a control/safety SITL, **not** a certified autopilot. It's the brain,
  proven cheaply — and now shown to cross-compile onto the MCU that would fly it.

---

*NIMBUS-9¾ v0.1 — "Magic? No. We just wrote the collision-avoidance really well."*
