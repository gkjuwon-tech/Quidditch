"""Error-state EKF: tight attitude, and robust closed-loop estimation through wind.

These assert the properties that matter, with generous bounds so they pass
across noise seeds. The headline (EKF ~2 deg / ~5 cm in gusting wind vs the
complementary filter diverging) is demonstrated in scenarios/run.py.
"""

import numpy as np

from nimbus_fc.core import math3d as M
from nimbus_fc.core.types import RiderIntent, State
from nimbus_fc.safety.commander import Commands
from nimbus_fc.sim.rider import RiderScript, Segment
from nimbus_fc.sim.simulator import Simulator
from nimbus_fc.sim.wind import Wind


def _launch(*extra):
    return RiderScript([
        Segment(0.0, cmd=Commands(arm=True)),
        Segment(0.5, cmd=Commands(takeoff=True)),
        *extra,
    ])


def test_ekf_attitude_tight_at_hover():
    sim = Simulator(initial=State(pos=np.array([0.0, 0.0, 0.0])),
                    state_source="estimate", estimator="ekf", seed=1)
    sim.run(15.0, lambda t, s: _launch(Segment(8.0, intent=RiderIntent()))(t))
    t, e = sim.dyn.state, sim.estimator
    att_err = np.rad2deg(np.linalg.norm(M.quat_error_angle_axis(t.quat, e.q)))
    pos_err = np.linalg.norm(t.pos - e.pos)
    assert att_err < 3.0, f"hover attitude estimate loose: {att_err:.2f} deg"
    assert pos_err < 0.3, f"hover position estimate loose: {pos_err:.2f} m"


def test_fly_on_estimate_through_wind_stays_controlled():
    """EKF + gravity/mag fusion must keep control flying on the estimate in
    gusting wind -- the case where the complementary filter diverged."""
    for seed in range(4):
        wind = Wind(steady=(6.0, -3.0, 0.0), gust_sigma=1.5, gust_tau=1.5, seed=seed)
        sim = Simulator(initial=State(pos=np.array([0.0, 0.0, 0.0])),
                        state_source="estimate", estimator="ekf", wind=wind, seed=seed)
        script = _launch(
            Segment(7.0, intent=RiderIntent(pitch=0.7, roll=0.4)),
            Segment(14.0, intent=RiderIntent(yaw=0.5, lift=0.4)),
            Segment(20.0, intent=RiderIntent()),
        )
        sim.run(28.0, lambda t, s: script(t))
        t, e = sim.dyn.state, sim.estimator
        att_err = np.rad2deg(np.linalg.norm(M.quat_error_angle_axis(t.quat, e.q)))
        assert sim.fc.geofence.contains(t.pos), f"seed {seed}: left the pitch"
        assert t.speed < 2.0, f"seed {seed}: not settled ({t.speed:.2f} m/s)"
        assert att_err < 12.0, f"seed {seed}: attitude estimate loose ({att_err:.1f} deg)"


def test_ekf_beats_complementary_attitude_in_wind():
    """The EKF's attitude estimate should be much tighter than the
    complementary filter under the same gusty conditions."""
    def final_att_err(estimator):
        wind = Wind(steady=(6.0, -3.0, 0.0), gust_sigma=1.5, gust_tau=1.5, seed=5)
        sim = Simulator(initial=State(pos=np.array([0.0, 0.0, 0.0])),
                        state_source="estimate", estimator=estimator, wind=wind, seed=5)
        sim.run(20.0, lambda t, s: _launch(
            Segment(7.0, intent=RiderIntent(pitch=0.6, roll=0.3)),
            Segment(14.0, intent=RiderIntent()))(t))
        t, e = sim.dyn.state, sim.estimator
        return np.rad2deg(np.linalg.norm(M.quat_error_angle_axis(t.quat, e.q)))

    assert final_att_err("ekf") < final_att_err("complementary")
