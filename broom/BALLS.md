# ⚽ The Balls — autonomous Quaffle, Bludger & Golden Snitch

> Three flying balls that chase, flee, get caught, and score — and **physically
> cannot hit a person**. The menace is real; the contact is software.

```bash
python scenarios/balls.py match     # all three + four players at once
python scenarios/balls.py snitch    # evasion: 1 seeker can't catch it
python scenarios/balls.py bludger   # pursuit + soft-tag, zero contact
python scenarios/balls.py quaffle   # catch / carry / throw / score
```

This is **Phase 1 of the balls** for the [Real Quidditch project](../QUIDDITCH_REALITY_PROJECT.md):
the guidance, evasion, pursuit and multi-agent safety, proven in simulation.

> 🏟️ For the **full match** — these balls plus *real broom-flown players* and a
> central **Dementor** referee (deconfliction, send-offs, scoring, the +150
> capture) — see **[MATCH.md](MATCH.md)** (`python scenarios/match.py seek`).

---

## The design call

A ball *is* a small agile drone. Its inner attitude/thrust loop is the broom's
proven control cascade (`nimbus_fc.control`) — so here each ball is modelled as
an **acceleration- and speed-limited agent**, and all the effort goes into the
genuinely new part: **autonomous guidance and the no-contact guarantee.**

```
   guidance (per ball) ─► NO-CONTACT AVOIDANCE ─► pitch bounds ─► agent motion
   (evade / pursue /         (the unbreakable
    catch+throw)              safety floor)
```

The `World` steps every player and ball together and is the referee: it sees
everyone and enforces the one rule that matters.

---

## The unbreakable rule: a ball never drives into a person

`ball/avoidance.py` sits under **every** ball, gentle or aggressive. Using the
same stopping-distance profile that keeps the broom inside the pitch — here
applied to people, and accounting for the *person's* motion too — it clamps a
ball's commanded velocity so its **padded shell decelerates to a stop at the
safety distance** from anyone, and actively retreats if crowded.

`safety_radius` is literally the foam shell. So:
- separation **≥ 0** → the shell never even touched anyone (the normal case);
- the rare graze during an adversarial pin is absorbed by the foam — *that's
  the "soft tag" design: it doesn't hurt, it's just embarrassing.*

Measured: across a 40 s **match with all three balls and four players**, the
worst shell-to-body clearance of *any* ball to *any* person was **+0.48 m** —
the invariant held on every tick.

---

## 🟡 Golden Snitch — predictive evasion (`ball/snitch.py`)

Its whole job is to not be caught:
1. **Predict** each seeker's reaching hand a step ahead and flee where the hand
   *will be*, not where it is.
2. **Juke** — a tangential, periodically-flipping feint so escape is never a
   straight line a seeker can intercept.
3. **Don't get cornered** — repel from walls; pop into the 3rd dimension when
   pinned.
4. **Fatigue handicap** — top speed decays slowly so the game actually ends.

Capture needs a hand held within `capture_radius` for `capture_dwell` seconds
(you must *close your hand*, not brush it).

| seekers | outcome |
|--------:|---------|
| 1 | **never caught** (survives indefinitely) |
| 3, coordinated | caught in ~10 s |

## ⚫ Bludger — pursuit + soft-tag (`ball/bludger.py`)

The skull-cracker, with the skull-cracking removed. `HUNT → TAG → RETREAT`:
lead-pursuit intercept, then at ~1.5 m it registers a **HIT in software and
peels away**. Because the tag radius sits *outside* the no-contact floor, the
shell never has to reach the person — a bat swing inside `bat_radius` deflects
it. In a 30 s chase it landed **8 tags, worst shell clearance +0.40 m,
closest-approach speed ~0 m/s**: all threat, no contact.

## 🔴 Quaffle — catch / carry / throw / score (`ball/quaffle.py`)

The friendly one: soft hover, generous catch radius, rides with its holder,
then is thrown at the nearest hoop with a tunable **aim-assist** (forgiving for
a youth league, off for the pros) and scores on pass-through. Still wrapped in
the same no-contact layer — even the nice ball won't bonk you.

---

## Layout

```
nimbus_fc/ball/
  params.py      Quaffle / Bludger / Snitch presets (size, agility, behaviour knobs)
  body.py        BallBody (accel-limited agent) + Player (kinematic, with reach)
  avoidance.py   the no-contact safety floor (shared by all balls)
  snitch.py      predictive evasion
  bludger.py     pursuit + soft-tag state machine
  quaffle.py     catch / carry / throw-assist / score
  policies.py    simple seeker/evader AIs for scenarios
  world.py       multi-agent arena + hoops + scoring + event log
scenarios/balls.py   snitch | bludger | quaffle | match
tests/test_balls.py  evasion, soft-tag-without-contact, scoring, match safety
```

## Honest limitations

- Balls are guidance-level agents (accel/speed-limited); the full 6-DOF inner
  loop is the broom cascade, not re-flown per ball here.
- Players are kinematic with scripted/seeker policies — not the full broom EKF
  stack (that integration is the natural next step toward a real match sim).
- "No contact" is guaranteed for the ball's *own* motion; a person who rams a
  ball faster than it can retreat meets the foam shell — which is the point of
  the foam shell.

*"Magic? No. We just wrote the collision-avoidance really well."*
