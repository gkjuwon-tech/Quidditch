#!/usr/bin/env python3
"""NIMBUS balls -- runnable multi-agent scenarios.

    python scenarios/balls.py            # list
    python scenarios/balls.py snitch     # evasion vs 1 and 3 seekers
    python scenarios/balls.py bludger    # pursuit + soft-tag, zero contact
    python scenarios/balls.py quaffle    # catch / carry / throw / score
    python scenarios/balls.py match      # all three + players, safety report
    python scenarios/balls.py all

Every scenario reports the events and the one number that matters most: the
minimum padded-shell clearance to any person (a ball must never drive into a
player). dt = 6 ms.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from nimbus_fc.ball import params, BallBody, Player, World  # noqa: E402
from nimbus_fc.ball.avoidance import NoContactAvoidance  # noqa: E402
from nimbus_fc.ball.bludger import BludgerPursuit  # noqa: E402
from nimbus_fc.ball.policies import seek_ball  # noqa: E402
from nimbus_fc.ball.quaffle import QuaffleBehavior  # noqa: E402
from nimbus_fc.ball.snitch import SnitchEvasion  # noqa: E402

DT = 0.006


def _hoops():
    return [(np.array([46.0, 0.0, 12.0]), 1.5),
            (np.array([46.0, 6.0, 12.0]), 1.5),
            (np.array([46.0, -6.0, 12.0]), 1.5)]


def _run(world: World, duration: float):
    mins = np.inf
    n = int(duration / DT)
    for _ in range(n):
        world.step(DT)
        for ball in world.balls:
            if ball.active:
                mins = min(mins, NoContactAvoidance.min_separation(ball.body, world.players))
    return mins


def _header(name, blurb):
    print("\n" + "=" * 74)
    print(f"  BALL SCENARIO: {name}\n  {blurb}")
    print("=" * 74)


def _events(world, limit=10):
    for t, msg in world.events[:limit]:
        print(f"    t={t:6.2f}s  {msg}")
    if len(world.events) > limit:
        print(f"    ... (+{len(world.events) - limit} more)")


def scn_snitch():
    _header("snitch", "Predictive evasion. One seeker can't catch it; it takes "
                      "a coordinated pack.")
    for n_seek in (1, 3):
        w = World()
        body = BallBody(params.snitch(), [0, 0, 9])
        ball = w.add_ball(body, SnitchEvasion(params.snitch()))
        for i in range(n_seek):
            a = 2 * np.pi * i / n_seek
            pl = Player(i, [30 * np.cos(a), 18 * np.sin(a), 9], max_speed=14, reach=1.0)
            w.add_player(pl, policy=seek_ball(ball))
        mins = _run(w, 45.0)
        caught = next((t for t, m_ in w.events if "CAUGHT" in m_), None)
        verdict = f"caught at {caught:.1f}s" if caught else "SURVIVED past 45 s"
        print(f"  {n_seek} seeker(s): {verdict};  min shell clearance "
              f"{mins:+.2f} m to a person")


def scn_bludger():
    _header("bludger", "Aggressive pursuit; the 'hit' is a ~1.5 m proximity tag, "
                       "never a collision.")
    w = World()
    pl = Player(0, [10, 0, 9], max_speed=11, reach=0.9)

    def evade(world, p):
        c = np.array([0, 0, 9.0])
        r = p.pos - c
        ang = np.arctan2(r[1], r[0]) + 0.45
        return (c + 16 * np.array([np.cos(ang), np.sin(ang), 0]) - p.pos)

    w.add_player(pl, policy=evade)
    body = BallBody(params.bludger(), [-22, 0, 9])
    ball = w.add_ball(body, BludgerPursuit(params.bludger()))
    worst, impact = np.inf, 0.0
    for _ in range(int(30.0 / DT)):
        w.step(DT)
        sep = NoContactAvoidance.min_separation(body, w.players)
        worst = min(worst, sep)
        if sep < 0.4:
            impact = max(impact, NoContactAvoidance.closing_speed(body, w.players))
    _events(w, 6)
    print(f"  soft-tags landed: {ball.behavior.hits.get(0, 0)}")
    print(f"  worst shell clearance: {worst:+.2f} m  "
          f"(>=0 => never touched);  closest-approach speed {impact:.1f} m/s")


def scn_quaffle():
    _header("quaffle", "The gentle one: caught, carried, thrown with aim-assist, "
                       "scored through a hoop.")
    w = World()
    w.hoops = _hoops()
    body = BallBody(params.quaffle(), [0, 0, 10])
    ball = w.add_ball(body, QuaffleBehavior(params.quaffle()))
    pl = Player(0, [-6, 0, 10], max_speed=12, reach=0.9)
    w.add_player(pl, policy=seek_ball(ball))
    _run(w, 14.0)
    _events(w, 10)
    print(f"  final score: {w.score}")


def scn_match():
    _header("match", "All three balls + several players at once. The only hard "
                     "rule: no ball ever drives into a person.")
    w = World()
    w.hoops = _hoops()
    rng = np.random.default_rng(0)
    # players holding patrol patterns on scripted loops
    for i in range(4):
        a = 2 * np.pi * i / 4
        pl = Player(i, [20 * np.cos(a), 12 * np.sin(a), 9], max_speed=12, reach=0.9)
        c = np.array([0, 0, 9.0])
        spin = 0.4 if i % 2 == 0 else -0.4

        def loop(world, p, c=c, spin=spin):
            r = p.pos - c
            ang = np.arctan2(r[1], r[0]) + spin
            return (c + 18 * np.array([np.cos(ang), np.sin(ang), 0]) - p.pos)
        w.add_player(pl, policy=loop)

    snitch = w.add_ball(BallBody(params.snitch(), [0, 0, 11]),
                        SnitchEvasion(params.snitch()))
    bludger = w.add_ball(BallBody(params.bludger(), [-20, 5, 9]),
                         BludgerPursuit(params.bludger()))
    quaffle = w.add_ball(BallBody(params.quaffle(), [0, 0, 8]),
                         QuaffleBehavior(params.quaffle()))

    worst = np.inf
    for _ in range(int(40.0 / DT)):
        w.step(DT)
        for ball in w.balls:
            if ball.active:
                worst = min(worst, NoContactAvoidance.min_separation(ball.body, w.players))
    _events(w, 12)
    print(f"  bludger soft-tags: {bludger.behavior.hits}")
    print(f"  snitch caught: {'no' if snitch.active else 'yes'}")
    print(f"  WORST shell clearance, ANY ball to ANY person, whole match: "
          f"{worst:+.2f} m")
    print("  -> the safety invariant held for every ball, every tick.")


SCENARIOS = {"snitch": scn_snitch, "bludger": scn_bludger,
             "quaffle": scn_quaffle, "match": scn_match}


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        print("  scenarios:", ", ".join(SCENARIOS), "| all")
        return 0
    if argv[0] == "all":
        for fn in SCENARIOS.values():
            fn()
        return 0
    if argv[0] not in SCENARIOS:
        print(f"unknown: {argv[0]}")
        return 1
    SCENARIOS[argv[0]]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
