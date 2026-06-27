#!/usr/bin/env python3
"""NIMBUS full match -- broom-flown players + balls + the Dementor referee.

    python scenarios/match.py seek     # broom agents coordinate to catch the snitch
    python scenarios/match.py match    # integrated scenario: seekers, bludger, quaffle, keeper
    python scenarios/match.py kill      # master emergency stop
    python scenarios/match.py all

The players here are NOT scripted points -- each is a 6-DOF broom flown by the
full flight stack (commander + geofence + fly-by-intent + control cascade). the
Dementor keeps brooms from colliding and owns the rulebook. dt = 2.5 ms (400 Hz).
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from nimbus_fc.ball import params, BallBody, World  # noqa: E402
from nimbus_fc.ball.avoidance import NoContactAvoidance  # noqa: E402
from nimbus_fc.ball.bludger import BludgerPursuit  # noqa: E402
from nimbus_fc.ball.quaffle import QuaffleBehavior  # noqa: E402
from nimbus_fc.ball.snitch import SnitchEvasion  # noqa: E402
from nimbus_fc.core.params import Params  # noqa: E402
from nimbus_fc.match.broom_agent import BroomAgent  # noqa: E402
from nimbus_fc.match.dementor import Dementor  # noqa: E402
from nimbus_fc.match.policies import chase_ball, guard_hoops, patrol  # noqa: E402

DT = 0.0025
# when True, every broom flies on its own onboard EKF (noisy IMU+GNSS+mag)
# instead of truth state. set by --ekf. EKF runs decimated to 100 Hz.
_EKF = False


def _src():
    return "estimate" if _EKF else "truth"


def _match_snitch():
    """a snitch with a match-length fatigue handicap so the game can end."""
    sp = params.snitch()
    sp.extra["fatigue_tau"] = 25.0
    sp.extra["fatigue_floor"] = 0.40
    return sp


def _hoops():
    return [(np.array([46.0, 0.0, 12.0]), 1.6),
            (np.array([46.0, 7.0, 12.0]), 1.6),
            (np.array([46.0, -7.0, 12.0]), 1.6)]


def _broom_pair_min(world):
    brooms = [p for p in world.players if hasattr(p, "rider_ai")]
    if len(brooms) < 2:
        return np.inf
    return min(np.linalg.norm(a.pos - b.pos)
               for i, a in enumerate(brooms) for b in brooms[i + 1:])


def _header(name, blurb):
    print("\n" + "=" * 74)
    print(f"  MATCH: {name}\n  {blurb}")
    print("=" * 74)


def _report(world, dem, mb, msep):
    for t, m_ in world.events[-14:]:
        print(f"    t={t:6.2f}s  {m_}")
    sb = dem.scoreboard(world)
    print(f"  scoreboard: quaffle {sb['quaffle_goals']}  + snitch {sb['snitch']}"
          f"  = {sb['total']}   (game_over={sb['game_over']})")
    print(f"  SAFETY: min broom-broom {mb:+.2f} m (contact ~0.8) | "
          f"min ball-to-person {msep:+.2f} m")


def scn_seek():
    _header("seek", "Two real broom-flown seekers coordinate to run down the "
                    "snitch; the Dementor keeps them from colliding.")
    w = World()
    snitch = w.add_ball(BallBody(_match_snitch(), [0, 0, 11]),
                        SnitchEvasion(_match_snitch()))
    for i in range(2):
        a = np.pi * i + 0.3
        w.players.append(BroomAgent(i, [30 * np.cos(a), 18 * np.sin(a), 10],
                                    chase_ball(snitch), params=Params(), state_source=_src(), ekf_div=4,reach=1.4))
    dem = Dementor(broom_sep=3.0, margin=2.0).attach(w)
    mb, msep = np.inf, np.inf
    for _ in range(int(60.0 / DT)):
        w.step(DT)
        mb = min(mb, _broom_pair_min(w))
        if snitch.active:
            msep = min(msep, NoContactAvoidance.min_separation(snitch.body, w.players))
        if dem.game_over:
            break
    _report(w, dem, mb, msep)
    print(f"  -> {'SNITCH CAUGHT, game over' if dem.game_over else 'snitch survived'} "
          f"at t={w.t:.1f}s")


def scn_match():
    _header("match", "Full chaos: broom seekers + a Bludger sending players off "
                     "+ a Quaffle being scored, all refereed at once.")
    w = World()
    w.hoops = _hoops()
    snitch = w.add_ball(BallBody(_match_snitch(), [0, 0, 12]),
                        SnitchEvasion(_match_snitch()))
    bludger = w.add_ball(BallBody(params.bludger(), [-26, 4, 9]),
                         BludgerPursuit(params.bludger()))
    quaffle = w.add_ball(BallBody(params.quaffle(), [-10, 0, 10]),
                         QuaffleBehavior(params.quaffle()))
    # two seekers chasing the snitch
    for i in range(2):
        a = np.pi * i + 0.3
        w.players.append(BroomAgent(i, [28 * np.cos(a), 16 * np.sin(a), 10],
                                    chase_ball(snitch), params=Params(), state_source=_src(), ekf_div=4,reach=1.4))
    # a chaser going for the quaffle, and a keeper guarding the hoops
    w.players.append(BroomAgent(2, [-14, 0, 10], chase_ball(quaffle),
                                params=Params(), state_source=_src(), ekf_div=4,reach=1.0))
    w.players.append(BroomAgent(3, [40, 0, 12], guard_hoops(w.hoops, quaffle),
                                params=Params(), state_source=_src(), ekf_div=4,reach=1.0))
    dem = Dementor(broom_sep=3.0, margin=2.0).attach(w)
    mb, msep = np.inf, np.inf
    for _ in range(int(50.0 / DT)):
        w.step(DT)
        mb = min(mb, _broom_pair_min(w))
        for b in w.balls:
            if b.active:
                msep = min(msep, NoContactAvoidance.min_separation(b.body, w.players))
        if dem.game_over:
            break
    _report(w, dem, mb, msep)
    print(f"  bludger send-offs: {bludger.behavior.hits}")


def scn_kill():
    _header("kill", "Master emergency stop: the Dementor sends every craft into "
                    "a controlled descent.")
    w = World()
    snitch = w.add_ball(BallBody(_match_snitch(), [0, 0, 12]),
                        SnitchEvasion(_match_snitch()))
    for i in range(3):
        a = 2 * np.pi * i / 3
        w.players.append(BroomAgent(i, [20 * np.cos(a), 12 * np.sin(a), 11],
                                    patrol([0, 0, 11]), params=Params(), state_source=_src(), ekf_div=4,reach=1.2))
    dem = Dementor().attach(w)
    for _ in range(int(4.0 / DT)):
        w.step(DT)
    alt_before = np.mean([p.pos[2] for p in w.players])
    dem.kill(w)
    for _ in range(int(8.0 / DT)):
        w.step(DT)
    alt_after = np.mean([p.pos[2] for p in w.players])
    print(f"    KILL pressed at t=4.0s")
    print(f"  mean broom altitude: {alt_before:.1f} m -> {alt_after:.1f} m "
          f"(all descending under control)")
    for t, m_ in dem.log:
        print(f"    t={t:5.2f}s  {m_}")


SCENARIOS = {"seek": scn_seek, "match": scn_match, "kill": scn_kill}


def main(argv):
    global _EKF
    argv = list(argv)
    if "--ekf" in argv:
        _EKF = True
        argv.remove("--ekf")
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        print("  scenarios:", ", ".join(SCENARIOS), "| all")
        print("  --ekf   fly every broom on its onboard EKF (noisy IMU+GNSS+mag)")
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
