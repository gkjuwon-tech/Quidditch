"""ball behaviours + the no-contact safety invariant."""

import numpy as np

from nimbus_fc.ball import params, BallBody, Player, World
from nimbus_fc.ball.avoidance import NoContactAvoidance
from nimbus_fc.ball.bludger import BludgerPursuit
from nimbus_fc.ball.policies import seek_ball
from nimbus_fc.ball.quaffle import QuaffleBehavior
from nimbus_fc.ball.snitch import SnitchEvasion

DT = 0.006


def _hoops():
    return [(np.array([46.0, 0.0, 12.0]), 1.5)]


def test_ball_never_drives_into_a_person():
    """a ball commanded straight at a person stops at its safety shell and
    never touches them -- the core no-contact guarantee. (a person ramming the
    ball is their own doing; the padded shell is there for exactly that.)"""
    class Seek:
        def __init__(self, t): self.t = np.array(t, float)
        def update(self, world, ball, dt): return (self.t - ball.body.pos) * 3.0

    w = World()
    pl = Player(0, [12, 0, 9], max_speed=14)            # stationary target
    w.add_player(pl, policy=lambda world, p: np.zeros(3))
    body = BallBody(params.bludger(), [-12, 0, 9])
    w.add_ball(body, Seek([12, 0, 9]))                  # drive straight at them
    worst = np.inf
    for _ in range(int(6.0 / DT)):
        w.step(DT)
        worst = min(worst, NoContactAvoidance.min_separation(body, w.players))
    assert worst >= 0.0, f"the ball touched the person: {worst:.2f} m"


def test_snitch_survives_a_single_seeker():
    w = World()
    body = BallBody(params.snitch(), [0, 0, 9])
    ball = w.add_ball(body, SnitchEvasion(params.snitch()))
    w.add_player(Player(0, [25, 0, 9], max_speed=14, reach=1.0),
                 policy=seek_ball(ball))
    for _ in range(int(30.0 / DT)):
        w.step(DT)
    assert ball.active, "a lone seeker should never catch the snitch"


def test_snitch_is_catchable_by_a_pack():
    w = World()
    body = BallBody(params.snitch(), [0, 0, 9])
    ball = w.add_ball(body, SnitchEvasion(params.snitch()))
    for i in range(3):
        a = 2 * np.pi * i / 3
        w.add_player(Player(i, [30 * np.cos(a), 18 * np.sin(a), 9],
                            max_speed=14, reach=1.0), policy=seek_ball(ball))
    for _ in range(int(40.0 / DT)):
        w.step(DT)
        if not ball.active:
            break
    assert not ball.active, "a coordinated pack should eventually catch it"


def test_bludger_soft_tags_without_contact():
    w = World()
    pl = Player(0, [10, 0, 9], max_speed=11, reach=0.9)

    def evade(world, p):
        c = np.array([0, 0, 9.0]); r = p.pos - c
        ang = np.arctan2(r[1], r[0]) + 0.45
        return c + 16 * np.array([np.cos(ang), np.sin(ang), 0]) - p.pos

    w.add_player(pl, policy=evade)
    body = BallBody(params.bludger(), [-22, 0, 9])
    ball = w.add_ball(body, BludgerPursuit(params.bludger()))
    worst = np.inf
    for _ in range(int(30.0 / DT)):
        w.step(DT)
        worst = min(worst, NoContactAvoidance.min_separation(body, w.players))
    assert ball.behavior.hits.get(0, 0) >= 3, "bludger should land several tags"
    assert worst >= 0.0, f"bludger touched the player: {worst:.2f} m"


def test_quaffle_can_be_caught_and_scored():
    w = World()
    w.hoops = _hoops()
    body = BallBody(params.quaffle(), [0, 0, 10])
    ball = w.add_ball(body, QuaffleBehavior(params.quaffle()))
    w.add_player(Player(0, [-6, 0, 10], max_speed=12, reach=0.9),
                 policy=seek_ball(ball))
    for _ in range(int(12.0 / DT)):
        w.step(DT)
    assert w.score >= 10, "quaffle should be caught, thrown, and scored"


def test_match_safety_invariant_holds():
    """all three balls + four players: no ball ever physically touches anyone."""
    w = World()
    w.hoops = _hoops()
    for i in range(4):
        a = 2 * np.pi * i / 4
        spin = 0.4 if i % 2 == 0 else -0.4

        def loop(world, p, spin=spin):
            c = np.array([0, 0, 9.0]); r = p.pos - c
            ang = np.arctan2(r[1], r[0]) + spin
            return c + 18 * np.array([np.cos(ang), np.sin(ang), 0]) - p.pos
        w.add_player(Player(i, [20 * np.cos(a), 12 * np.sin(a), 9],
                            max_speed=12, reach=0.9), policy=loop)
    w.add_ball(BallBody(params.snitch(), [0, 0, 11]), SnitchEvasion(params.snitch()))
    w.add_ball(BallBody(params.bludger(), [-20, 5, 9]), BludgerPursuit(params.bludger()))
    w.add_ball(BallBody(params.quaffle(), [0, 0, 8]), QuaffleBehavior(params.quaffle()))

    worst = np.inf
    for _ in range(int(30.0 / DT)):
        w.step(DT)
        for ball in w.balls:
            if ball.active:
                worst = min(worst, NoContactAvoidance.min_separation(ball.body, w.players))
    assert worst >= 0.0, f"a ball touched a person during the match: {worst:.2f} m"
