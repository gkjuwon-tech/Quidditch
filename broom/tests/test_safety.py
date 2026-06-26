"""End-to-end safety behaviour: the properties that let a non-pilot survive."""

import numpy as np

from nimbus_fc.core.types import RiderIntent, CommanderState, State
from nimbus_fc.safety.commander import Commands
from nimbus_fc.sim.rider import RiderScript, Segment
from nimbus_fc.sim.simulator import Simulator


def _arm_and_takeoff(extra):
    return RiderScript([
        Segment(0.0, cmd=Commands(arm=True)),
        Segment(0.5, cmd=Commands(takeoff=True)),
        *extra,
    ])


def test_neutral_sticks_hold_position():
    """Let go of the controls -> the broom parks in the air."""
    sim = Simulator(initial=State(pos=np.array([0.0, 0.0, 0.0])))
    script = _arm_and_takeoff([Segment(8.0, intent=RiderIntent())])
    sim.run(20.0, lambda t, s: script(t))
    tail = [r for r in sim.log.rows if r["t"] > 16.0]
    drift = np.std([r["x"] for r in tail]) + np.std([r["y"] for r in tail])
    assert drift < 0.2, f"position hold drifted: {drift:.3f} m"
    assert sim.fc.state == CommanderState.FLYING


def test_geofence_keeps_vehicle_inside_pitch():
    """Slam every stick to the wall; never leave the hard boundary -- including
    a long full-throttle climb to the high (150 m) Quidditch ceiling."""
    sim = Simulator()
    script = _arm_and_takeoff([
        Segment(8.0, intent=RiderIntent(lift=1.0)),               # climb to the ceiling
        Segment(45.0, intent=RiderIntent(pitch=1.0, roll=1.0)),   # then slam the walls
        Segment(58.0, intent=RiderIntent(pitch=-1.0, roll=-1.0)), # up high
    ])
    sim.run(75.0, lambda t, s: script(t))
    reached = max(r["z"] for r in sim.log.rows)
    assert reached > 120.0, f"never actually climbed near the ceiling: {reached:.1f} m"
    for r in sim.log.rows:
        assert -50.0 <= r["x"] <= 50.0, f"x left pitch: {r['x']:.2f}"
        assert -25.0 <= r["y"] <= 25.0, f"y left pitch: {r['y']:.2f}"
        assert r["z"] <= 150.6, f"punched the ceiling: {r['z']:.2f}"


def test_kill_switch_is_a_gentle_descent_not_a_drop():
    """The big red button must NOT free-fall a manned vehicle."""
    sim = Simulator(initial=State(pos=np.array([0.0, 0.0, 0.0])))
    script = _arm_and_takeoff([
        Segment(8.0, intent=RiderIntent()),
        Segment(10.0, cmd=Commands(kill=True)),
    ])
    sim.run(30.0, lambda t, s: script(t))
    after_kill = [r for r in sim.log.rows if r["t"] > 10.2]
    max_descent = max(-r["vz"] for r in after_kill)
    assert max_descent < 2.5, f"descent too fast for a 'kill': {max_descent:.2f} m/s"
    assert sim.fc.state == CommanderState.DISARMED, "did not finish landed/disarmed"
    assert sim.log.rows[-1]["z"] < 0.3, "never reached the ground"


def test_battery_failsafe_returns_to_pit_and_lands():
    """Low battery seizes control, flies home, lands, disarms."""
    sim = Simulator(initial=State(pos=np.array([20.0, 10.0, 0.0])),
                    initial_soc=0.28)  # below RTP threshold
    script = _arm_and_takeoff([Segment(8.0, intent=RiderIntent(pitch=0.5))])
    sim.run(60.0, lambda t, s: script(t))
    assert sim.fc.state == CommanderState.DISARMED
    final = sim.log.rows[-1]
    pit = sim.p.pit_location
    assert abs(final["x"] - pit[0]) < 3.0 and abs(final["y"] - pit[1]) < 3.0, \
        "did not land at the pit"
    assert final["z"] < 0.3
