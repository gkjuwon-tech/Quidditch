"""The capstone: real broom-flown players + the Dementor referee."""

import numpy as np

from nimbus_fc.ball import params, BallBody, World
from nimbus_fc.ball.bludger import BludgerPursuit
from nimbus_fc.ball.snitch import SnitchEvasion
from nimbus_fc.core.params import Params
from nimbus_fc.match.broom_agent import BroomAgent
from nimbus_fc.match.dementor import Dementor
from nimbus_fc.match.policies import chase_ball, patrol

DT = 0.0025


def _match_snitch():
    sp = params.snitch()
    sp.extra["fatigue_tau"] = 25.0
    sp.extra["fatigue_floor"] = 0.40
    return sp


def test_broom_agent_flies_stably_to_a_target():
    """A player flown by the full FC stack reaches its goal without flipping."""
    class W:
        t = 0.0
    w = W()
    target = np.array([20.0, 10.0, 12.0])
    agent = BroomAgent(0, [-10, 0, 8], lambda world, me: (target - me.pos) * 0.8)
    for i in range(int(14.0 / DT)):
        w.t = i * DT
        agent.act(w, DT)
    assert np.linalg.norm(agent.pos - target) < 2.5, "broom didn't reach the goal"
    assert abs(np.rad2deg(agent.dyn.state.euler[0])) < 30.0, "broom flipped"


def test_dementor_keeps_brooms_from_colliding():
    w = World()
    snitch = w.add_ball(BallBody(params.snitch(), [0, 0, 10]),
                        SnitchEvasion(params.snitch()))
    # two brooms starting close, both diving at the same snitch
    w.players.append(BroomAgent(0, [-3, -15, 10], chase_ball(snitch), params=Params()))
    w.players.append(BroomAgent(1, [3, -15, 10], chase_ball(snitch), params=Params()))
    Dementor(broom_sep=3.0, margin=2.0).attach(w)
    worst = np.inf
    for _ in range(int(18.0 / DT)):
        w.step(DT)
        worst = min(worst, np.linalg.norm(w.players[0].pos - w.players[1].pos))
    assert worst > 0.8, f"brooms collided: {worst:.2f} m apart"


def test_snitch_capture_ends_the_game_with_150():
    w = World()
    sp = _match_snitch()
    snitch = w.add_ball(BallBody(sp, [0, 0, 11]), SnitchEvasion(sp))
    for i in range(2):
        a = np.pi * i + 0.3
        w.players.append(BroomAgent(i, [30 * np.cos(a), 18 * np.sin(a), 10],
                                    chase_ball(snitch), params=Params(), reach=1.4))
    dem = Dementor(broom_sep=3.0, margin=2.0).attach(w)
    for _ in range(int(55.0 / DT)):
        w.step(DT)
        if dem.game_over:
            break
    assert dem.game_over and not snitch.active, "two seekers should catch the snitch"
    assert dem.scoreboard(w)["snitch"] == 150


def test_bludger_tag_sends_a_player_off():
    w = World()
    seeker = BroomAgent(0, [8, 0, 9], patrol([0, 0, 9], radius=8.0),
                        params=Params(), reach=0.9)
    w.players.append(seeker)
    w.add_ball(BallBody(params.bludger(), [-18, 0, 9]), BludgerPursuit(params.bludger()))
    dem = Dementor().attach(w)
    penalised = False
    for _ in range(int(15.0 / DT)):
        w.step(DT)
        if seeker.tagged_out:
            penalised = True
            break
    assert penalised, "a tagged player should be sent off by the Dementor"
    assert any("sent off" in m for _, m in dem.log)


def test_master_kill_brings_everyone_down():
    w = World()
    for i in range(3):
        a = 2 * np.pi * i / 3
        w.players.append(BroomAgent(i, [18 * np.cos(a), 11 * np.sin(a), 12],
                                    patrol([0, 0, 12]), params=Params()))
    dem = Dementor().attach(w)
    for _ in range(int(2.0 / DT)):
        w.step(DT)
    before = np.mean([p.pos[2] for p in w.players])
    dem.kill(w)
    for _ in range(int(6.0 / DT)):
        w.step(DT)
    after = np.mean([p.pos[2] for p in w.players])
    assert after < before - 2.0, "kill switch should bring the brooms down"
