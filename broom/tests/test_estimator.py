"""estimator-in-the-loop test: the controller flies on the noisy estimate
(synthetic IMU + GNSS), never the truth, and must still reach the target.
"""

import numpy as np

from nimbus_fc.control.attitude import AttitudeController
from nimbus_fc.control.mixer import Mixer
from nimbus_fc.control.position import PositionController
from nimbus_fc.control.rate import RateController
from nimbus_fc.core import math3d as M
from nimbus_fc.core.params import Params
from nimbus_fc.core.types import Setpoint, State
from nimbus_fc.estimation.estimator import Estimator
from nimbus_fc.sim.dynamics import Dynamics
from nimbus_fc.sim.sensors import SensorSuite


def _fly_on_estimate(seed: int):
    """fly a step maneuver using ONLY the estimate; return (target_err, max_att_err_deg)."""
    p = Params()
    init = State(pos=np.array([0.0, 0.0, 5.0]))
    d = Dynamics(p, init)
    d.fan_thrust[:] = p.hover_thrust / p.num_fans
    sens = SensorSuite(p, seed=seed)
    est = Estimator(p, init)
    mix, pos = Mixer(p), PositionController(p)
    att, rate = AttitudeController(p), RateController(p)

    sp = Setpoint(pos=np.array([8.0, 6.0, 8.0]), yaw=0.3)
    coll, q_des, yff = p.hover_thrust, np.array([1.0, 0, 0, 0]), 0.0
    att_err = []
    for i in range(int(20.0 / p.dt)):
        es = est.state
        if i % p.pos_loop_div == 0:
            coll, q_des, yff = pos.update(sp, es, p.dt * p.pos_loop_div)
        gyro, acc = sens.imu(d.state, d.accel_world)
        rate_sp = att.update(es.quat, q_des, yff)
        tau = rate.update(rate_sp, gyro - est.gyro_bias, p.dt)
        fan, _ = mix.allocate(coll, tau)
        d.step(fan, p.dt)
        est.predict(gyro, acc, p.dt)
        if i % 8 == 0:                       # 50 Hz GNSS/RTK fix
            gp, gv = sens.gnss(d.state)
            est.fuse_gnss(gp, gv, p.dt * 8)
        att_err.append(np.linalg.norm(M.quat_error_angle_axis(d.state.quat, est.q)))
    return np.linalg.norm(d.state.pos - sp.pos), np.rad2deg(np.max(att_err))


def test_fly_on_estimate_stays_bounded_all_seeds():
    """flying on the noisy estimate must always remain controlled and settle
    near the target. the complementary filter isn't as crisp as truth-state
    SITL (a few metres of settling spread under worst-case noise is expected),
    but it never loses control."""
    for seed in range(8):
        target_err, max_att = _fly_on_estimate(seed)
        assert target_err < 5.0, f"seed {seed}: lost the target ({target_err:.2f} m)"
        # transient attitude-estimate error during hard accel can be large on a
        # complementary filter (an EKF would do better) -- but it has to stay
        # bounded and recover; steady-state tightness is checked separately.
        assert max_att < 35.0, f"seed {seed}: attitude estimate diverged ({max_att:.1f} deg)"


def test_attitude_estimate_steady_state_is_tight():
    """at hover the estimate should lock on within a couple of degrees."""
    p = Params()
    init = State(pos=np.array([0.0, 0.0, 5.0]))
    d = Dynamics(p, init)
    d.fan_thrust[:] = p.hover_thrust / p.num_fans
    sens = SensorSuite(p, seed=7)
    est = Estimator(p, init)
    fan = np.full(p.num_fans, p.hover_thrust / p.num_fans)
    err = []
    for i in range(int(10.0 / p.dt)):
        gyro, acc = sens.imu(d.state, d.accel_world)
        d.step(fan, p.dt)
        est.predict(gyro, acc, p.dt)
        if i % 20 == 0:
            gp, gv = sens.gnss(d.state)
            est.fuse_gnss(gp, gv, p.dt * 20)
        if d.state.t > 7.0:
            err.append(np.linalg.norm(M.quat_error_angle_axis(d.state.quat, est.q)))
    assert np.rad2deg(np.mean(err)) < 3.0
