# 🧹 NIMBUS-9¾ — Hardware Full-Stack

> The flight software was the brain. **This is the body.** A bill of materials,
> parametric OpenSCAD CAD, a PDF drawing package, *and* the two things that make
> it a real product and not a render: a **flight + thermal budget that closes**,
> and a **firmware HAL** that lets the existing `nimbus_fc` stack actually drive
> the hardware.
>
> Every dimension here ties back to a number the software already flies with
> (`broom/nimbus_fc/...`). The hardware isn't decoration on the sim — it's the
> same airframe, in atoms.

```
hardware/
  cad/            parametric OpenSCAD models (broom + 3 balls) + lib/
  bom/            per-part CSV bills of materials + SUMMARY.csv rollup
  firmware/       hal.py (software<->stick bridge + thermal governor) + pinmap.csv
  analysis/       flight_thermal.py — does a broomstick actually fly + stay cool?
  scripts/        render.sh (CAD -> PNG), make_pdf.py (drawing package)
  drawings/       the committed PDF drawing package  (generated)
  renders/        committed hero renders + sheet previews (generated)
  Makefile        make check | cad | pdf | all
```

---

## The design call: preserve the silhouette, hide the engineering

The reference is a **broom**: a thin handle and a full bristle leaf. So that's
what the hardware *is* — no pods, no outriggers, no helicopter. The ducted fans
live **inside the shaft and the bristle shroud** (prop exposure 0). Same rule for
the balls: outside is a soft padded shell, inside is the swarm.

| Part | Canon shape kept | Where the drive hides | True to software |
|------|------------------|-----------------------|------------------|
| **Broom** | thin handle + bristle leaf | 8 EDFs in shaft + bristle shroud | `core/params.py` fan layout, mass, battery |
| **Golden Snitch** | walnut sphere **+ real wings** | 4 micro-EDF swarm core | `ball/params.py snitch` (R 0.04 m, 50 g) |
| **Bludger** | black iron-look sphere | 4 EDF swarm core | `ball/params.py bludger` (R 0.15 m) |
| **Quaffle** | red grippy sphere | 4 EDF swarm core | `ball/params.py quaffle` (R 0.18 m) |

![broom](renders/broom.png)

### The Snitch's open secret 🤫
The Snitch is the one canon ball with wings, so it gets **real flapping ones** on
coreless gearmotors — thin enough to genuinely flutter. The official story is
that the wings make it fly. They don't; the internal micro-EDF swarm does
(`bom/snitch_bom.csv` SNT-02/03 vs SNT-05). The wings are theatre. *Do not
explain this to Potterheads.*

---

## Does a broomstick actually fly? (the honest part)

A bare stick has almost no disc area, so we did the real budget instead of
hand-waving. `make check`:

```
[1] THRUST     T/W 2.45  -> hovers at 41% throttle           PASS
[2] POWER      disc area capped by the bristle flare -> 10.7 kPa, ~153 kW hover
[3] ENDURANCE  ~61 s per charge  -> a SPRINTER, by design (hot-swap pits)
[4] THERMAL    28 kW waste heat vs 224 kW air-cooling -> 8.1x margin  PASS
VERDICT: the budget CLOSES. It flies, and it does not melt.
```

> **Honest geometry note.** The lift fan is sized to fit *entirely inside the
> bristle flare* — it does not protrude in any non-cutaway view (verify:
> `make cad`, compare `renders/broom.png` vs `renders/broom_cutaway.png`). That
> flare frontal area is the hard ceiling on disc area, which is exactly why
> battery-only endurance is ~1 minute. No oversized fan hidden behind thin bristles.

---

## Wave it to fly it (gesture control)

The flight software already turns a normalized `RiderIntent(pitch, roll, yaw,
lift)` into a safe, velocity-capped setpoint (`nimbus_fc/intent/mapper.py`) — so
the hardware just needs to read the rider physically waving the broom and emit
that intent. `firmware/rider_input.py` does exactly that, and its demo runs the
gesture **through the real `IntentMapper`**:

```
lean forward -> commanded velocity [fwd +12.5, right +0.0, up +0.0] m/s (cap 16)
lean right   -> commanded velocity [fwd +0.0,  right +12.5, up +0.0] m/s
throttle up  -> commanded velocity [fwd +0.0,  right +0.0,  up +2.8] m/s
hands off    -> [0, 0, 0]  (auto-hover — let go and it parks in the air)
```

Handle pose (lean/twist from the handle IMU) + a thumb throttle → intent. Wave
it up/down/left/right and it flies that way — and you *can't* crash it by being
bad, because the mapper caps every wish to the flight envelope.

---

## Flying a whole match (series-hybrid)

Battery-only, the broom is a ~60 s sprinter — that's just the physics of having
no disc area. You can't out-battery it (30 min at ~150 kW ≈ 75 kWh ≈ 400 kg of
cells). With **form and power both fixed**, the only lever is *energy density*,
and liquid fuel beats li-ion ~48×. So `analysis/endurance_match.py` sizes a
**series-hybrid range extender**: a slim in-shaft **micro-turbine genset** burns
sustainable aviation fuel to make the match-average power, while the existing
2600 Wh battery becomes the **peak buffer** (full ~250 kW bursts unchanged).

```
fuel carried .... 15 kg SAF (53 kWh usable)
all-up mass ..... 166 kg   (genset + fuel in the shaft)
thrust-to-weight  1.77     (still hovers at 57% of max)
MATCH FLIGHT .... ~26 min   >= a full match.   PASS
```

The honest cost: it's heavier, T/W drops from 2.45 to 1.77, and the turbine
exhaust is hot — vented through the bristle root via an ejector that mixes cool
bypass air (and ceramic-matrix bristle tips that take the heat and still
flutter). Form kept, peak power kept, match filled.

---

## Flying a whole match — the Snitch 🟡 (beamed power)

The Snitch has the *exact same* problem, shrunk to 50 g. A walnut-sized ball has
almost no disc area either, so 4 micro-EDFs hover at ~22 W out of a 1S 300 mAh
cell (~1.1 Wh) — a **~2.7 minute** sprint. (That's not a coincidence: the
guidance already fades the Snitch out at `fatigue_tau` **120 s** — the
"fatigue" was a dying **battery** all along.) `analysis/snitch_endurance.py`:

```
[1] BATTERY-ONLY  22 W hover on 1.1 Wh -> ~2.7 min sprint (≈ fatigue_tau)
[2] BEAMED POWER  5.8 GHz array, 25 m, 1.8% capture -> ~2.5 kW into the pitch
[3] BUFFERS       supercap fires the 32 m/s² jukes; LiPo rides out occlusion
VERDICT: form PASS (still 50 g) · agility PASS · MATCH FILLED, no pit.
```

The broom's lever was **energy density** (carry it as fuel). A 50 g ball can't
carry a turbine or fuel without blowing the canon walnut form, so the Snitch
**flips the lever: it doesn't carry the energy at all — it harvests it.** The
pitch becomes a powered volume: a perimeter **5.8 GHz phased array beams power
and steers the spot onto the Snitch** using the pose it already broadcasts to
the referee (`bom/snitch_bom.csv` SNT-19/20). The gold shell's **dimple vents
double as a conformal rectenna** (SNT-15/16) — the harvester *is* the shell, so
it adds ~0 mass. The 300 mAh cell becomes a **buffer**, exactly like the broom's
2600 Wh pack in the hybrid: a **supercap** (SNT-17) fires the full 32 m/s² juke
bursts, and the LiPo **rides through** the moment a player's body crosses the
beam. Harvested ≥ draw, continuously, anywhere in-bounds → a Snitch that flies a
whole match. Honest cost: ~2.5 kW pumped into the pitch, and it can only flee
where the beam reaches — which is the in-bounds volume it's repelled into
staying inside anyway. Build it by hand: **[SNITCH_ASSEMBLY_GUIDE.md](SNITCH_ASSEMBLY_GUIDE.md)**.

---

## Flying HIGH, like real Quidditch

Real Quidditch is vertical — far above 18 m. Climbing raises two honest
questions, both checked by `analysis/altitude_ceiling.py`:

- **Thrust falls with air density.** At 150 m the air is still 98 % of
  sea-level, costing <2 % thrust — the broom's *service ceiling is kilometres*
  (hover ceiling ~7.6 km light / ~4.8 km hybrid). The ceiling is a **rule, not a
  limit**.
- **A fall from 150 m is lethal.** So the whole-vehicle ballistic parachute
  becomes the safety net: a Ø7.6 m canopy for a 6.5 m/s touchdown, rocket-
  deployed to full open in ~45 m. Honest flip — **flying high is *safe* for the
  chute** (105 m to spare); the danger band is *below* 45 m, covered by the
  airbag skirt + perimeter net.

So the league simply raises the geofence: `fence_ceiling` 18 → **150 m**. The
mechanism already enforces whatever number it's given, now proven by the updated
`tests/test_safety.py` (full-throttle climb to 150 m, stays contained). 30/30
software tests still green.

```
[1] THRUST  150 m -> T/W 2.45->2.40 (sprint), service ceiling 5,374 m   PASS
[2] FALL    Ø7.6 m chute opens in 45 m, 105 m to spare from the ceiling  PASS
VERDICT: raise the ceiling and play real, vertical Quidditch.
```

Two honest conclusions, both already handled by the existing software:

- **Endurance is short** because the broom shape has no disc area. That's *fine*:
  the league runs F1-style hot-swap pits, and `nimbus_fc` already forces
  Return-To-Pit at 30 % SoC (`batt_rtp_soc`). The shape costs endurance; we pit.
- **Heat is the real trap** of stuffing high-RPM fans into a thin shaft. Solved
  by not sealing them: the **lift air is the coolant** (motors sit in the duct
  flow), with **heat pipes** spreading the rest over the 2.4 m shaft, and a
  **thermal governor** that derates thrust before the windings cook.

---

## Software ↔ stick: the HAL

`nimbus_fc` ends at the mixer, which emits a per-fan thrust command in **newtons**.
`firmware/hal.py` is the skin that turns those into **DShot** frames for the ESCs,
ingests the sensors back, and runs the **thermal governor**. `make check` runs its
self-test:

```
nimbus_hal self-test (8 fans, one at 113 C)
  DShot frame     : [1338, 1338, 1338, 1957, ...]
  governor active : True (fan 3 derated to 76% authority -> clamped)
  total thrust    : ... N  (weight to beat: 1177 N)
```

The hard real-time cascade stays in the **Rust core** (`rust/nimbus_core`, on the
Cortex-M4F); the HAL is the I/O around it. Pin/protocol map: `firmware/pinmap.csv`.

---

## Build it

```bash
# engineering checks (pure python, no deps)
make check

# CAD renders  (needs openscad; auto-uses xvfb when headless)
make cad

# the PDF drawing package + BOM rollup  (needs matplotlib)
make pdf      # -> drawings/NIMBUS_hardware_drawings.pdf

make all      # everything
```

OpenSCAD models are parametric — open any `cad/*.scad`, set `cutaway=true` to
reveal the internals (`make cad` renders both).

### Building one by hand (and flying it)

Buying the parts and assembling the broom in a lab? The full step-by-step build
+ first-flight manual is **[ASSEMBLY_GUIDE.md](ASSEMBLY_GUIDE.md)** — Phase A→G
assembly keyed to every BOM part (BRM-01…41), ground tie-down tests, the
power-on sequence, boarding, low-altitude flight, landing, shutdown, and
emergency procedures. (Disclaimer: it is also, deliberately, very funny.)

---

## Bill of materials

Per-part CSVs in `bom/`, each line cross-linked to the software module it serves.
`scripts/make_pdf.py` rolls them into `bom/SUMMARY.csv` — the hardware for one full
7-v-7 match (14 brooms + 1 quaffle + 2 bludgers + 1 snitch). See the drawing
package's final sheet for the costed rollup.

> *"Magic? No. We just wrote the collision-avoidance really well — and then we
> built the broom that runs it."*
