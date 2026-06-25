# 🏟️ The Match — broom-flown players + the Dementor referee

> The two halves, joined. Players are no longer scripted dots — each is a **6-DOF
> broom flown by the full flight stack**. A **central referee** keeps them from
> colliding and runs the rulebook. This is the capstone.

```bash
python scenarios/match.py seek    # two real brooms coordinate to catch the snitch
python scenarios/match.py match   # full chaos: seekers + Bludger send-offs + a Quaffle goal
python scenarios/match.py kill     # master emergency stop
```

---

## Players that actually fly (`match/broom_agent.py`)

A `BroomAgent` is a player whose position comes from the **6-DOF broom plant
driven by the real `FlightController`** (commander + geofence + fly-by-intent +
the control cascade). A rider-AI is the *inverse* of the intent mapper — it
turns a desired world velocity into stick intent:

```
chase goal ─► desired velocity ─► RiderIntent ─► FlightController ─► fans ─► Dynamics ─► new pos
```

It exposes the same surface the balls expect from a person (`pos`, `vel`,
`reach`, `hand_toward`, …), so the no-contact avoidance and catch logic work
unchanged. Optionally each player flies on its own onboard **EKF**
(`state_source="estimate"`). Verified: a broom-flown seeker chases the snitch
while holding stable attitude (roll ≤ ~12°), no flips.

The balance falls out naturally: **one seeker can't catch the snitch; two
coordinated seekers run it down** as its fatigue handicap bites (~34 s).

---

## The Dementor — central referee (`match/dementor.py`)

Named for the thing that watches everything and ends games. It does what no
single agent can:

**1. Deconfliction.** Broom-flown players have no inter-broom avoidance of their
own. The Dementor adds a symmetric separation push between brooms, so two
players diving for the same snitch never collide. Measured: two brooms diving at
one snitch close to **0.48 m without** the referee → held at **1.6 m with** it
(brooms are ~0.4 m radius; contact at ~0.8 m).

**2. Judgement + scoreboard.**
- a Bludger tag → the Dementor **sends that player off** for a penalty (they
  idle-drift; deconfliction still protects them);
- a Quaffle through a hoop → **+10**;
- catching the Snitch → **+150 and the match ends**.

**3. Master kill.** One call sends every craft into a controlled descent
(mean altitude 9 m → 3 m and falling, gently) — never a motor cut.

---

## What a match looks like

```
seek:   t=34.0s  SNITCH CAUGHT  +150  -> GAME OVER
        scoreboard 150;  min broom-broom +1.60 m;  min ball-to-person +0.90 m

match:  Bludger send-offs across all four players, a Quaffle goal (+10),
        the snitch harried the whole time;  min broom-broom +0.96 m (safe).
```

Across every match the two invariants the project exists to prove hold:
**brooms never collide with each other, and balls never drive into people.**
(In the most crowded chaos a padded shell can graze a sent-off, drifting player
— absorbed by the foam, which is the entire point of the foam.)

---

## Layout

```
nimbus_fc/match/
  broom_agent.py   BroomAgent (real FC stack) + velocity->intent inverse mapper
  policies.py      rider-AIs: chase_ball, patrol, guard_hoops
  dementor.py      central referee: deconfliction + judgement + scoreboard + kill
scenarios/match.py   seek | match | kill
tests/test_match.py  stable flight, deconfliction, capture-ends-game, send-off, kill
```

## Honest limitations

- Players fly on truth-state by default for match speed; per-agent EKF is wired
  and works, just heavier to run for many brooms at once.
- Capturing the snitch with *safely-separated* broom-flown seekers is genuinely
  hard — it leans on the fatigue handicap, exactly as a real game would need a
  way to end.
- Right-of-way is symmetric repulsion, not a full priority/rules engine.

*"Magic? No. We just wrote the collision-avoidance really well."*
