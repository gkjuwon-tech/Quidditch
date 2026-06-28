"""Outer loop: position/velocity/altitude -> collective + attitude setpoint.

The loop that makes "let go and it parks itself" actually true. Per axis the
cascade is:

    pos error --P--> velocity sp --PID--> accel sp

The accel setpoint turns into a gravity-compensated thrust vector. Its
direction is the attitude we want (tilt = accelerate), and its projection on
the current body-up axis is the collective. Tilt is hard-clamped, so the
broom physically can't bank itself into a corner it can't climb out of.

It's PX4's mc_pos_control, trimmed down to what a broom actually needs.
"""

from __future__ import annotations

import numpy as np

from ..core import math3d as m
from ..core.params import Params
from ..core.types import Setpoint, State
from .pid import PID


class PositionController:
    def __init__(self, params: Params):
        self.p = params
        self.vel_xy = PID(params.kp_vel_xy, params.ki_vel_xy, params.kd_vel_xy,
                          params.vel_i_limit)
        self.vel_z = PID(params.kp_vel_z, params.ki_vel_z, params.kd_vel_z,
                         params.vel_i_limit)

    def reset(self) -> None:
        self.vel_xy.reset()
        self.vel_z.reset()

    def update(self, sp: Setpoint, state: State, dt: float):
        """Return (collective_thrust_N, q_des, yaw_rate_ff)."""
        p = self.p
        pos, vel = state.pos, state.vel

        # --- horizontal: pos -> vel_sp -> accel_sp ---
        # the velocity setpoint follows a stopping-distance profile so we can
        # always pull up inside the accel budget (no overshoot that turns into
        # a flip). hold is per-axis; a NaN component drops to velocity mode on
        # that axis, e.g. hold laterally while climbing.
        vel_sp_xy = sp.vel_ff[:2].copy()
        if sp.pos is not None and np.all(np.isfinite(sp.pos[:2])):
            err_xy = sp.pos[:2] - pos[:2]
            dist = float(np.linalg.norm(err_xy))
            if dist > 1e-6:
                a_brake = 0.7 * p.max_accel_xy
                v_des = min(p.kp_pos_xy * dist,             # linear P near target
                            np.sqrt(2.0 * a_brake * dist),  # don't outrun braking
                            p.max_speed_xy)
                vel_sp_xy += (err_xy / dist) * v_des
        vel_sp_xy = m.clamp_norm(vel_sp_xy, p.max_speed_xy)
        acc_xy = self.vel_xy.update(vel_sp_xy, vel[:2], dt)
        acc_xy = m.clamp_norm(acc_xy, p.max_accel_xy)

        # --- vertical: alt -> climb_sp -> accel_sp ---
        vel_sp_z = sp.vel_ff[2]
        if sp.pos is not None and np.isfinite(sp.pos[2]):
            vel_sp_z += p.kp_pos_z * (sp.pos[2] - pos[2])
        vel_sp_z = float(np.clip(vel_sp_z, -p.max_descent_rate, p.max_climb_rate))
        acc_z = float(self.vel_z.update([vel_sp_z], [vel[2]], dt)[0])

        # desired world-frame thrust vector, gravity already added back in
        acc_sp = np.array([acc_xy[0], acc_xy[1], acc_z])
        thrust_vec = p.mass * acc_sp + np.array([0.0, 0.0, p.hover_thrust])
        thrust_vec = self._limit_tilt(thrust_vec)

        # collective is just that vector projected onto the current body-up
        body_z = m.quat_rotate(state.quat, np.array([0.0, 0.0, 1.0]))
        collective = float(np.dot(thrust_vec, body_z))
        collective = max(collective, 0.2 * p.hover_thrust)  # keep a floor, never free-fall

        # attitude target falls out of the thrust direction plus desired yaw
        yaw_des = sp.yaw if sp.yaw is not None else m.yaw_of(state.quat)
        q_des = self._attitude_from_thrust(thrust_vec, yaw_des)
        return collective, q_des, sp.yaw_rate_ff

    def _limit_tilt(self, thrust_vec: np.ndarray) -> np.ndarray:
        """Hold the thrust vector's tilt off vertical to <= params.max_tilt."""
        z = max(thrust_vec[2], 1e-3)
        xy = thrust_vec[:2]
        xy_norm = float(np.linalg.norm(xy))
        max_xy = z * np.tan(self.p.max_tilt)
        if xy_norm > max_xy and xy_norm > 1e-9:
            xy = xy * (max_xy / xy_norm)
        return np.array([xy[0], xy[1], z])

    def _attitude_from_thrust(self, thrust_vec: np.ndarray, yaw: float) -> np.ndarray:
        """Body->world rotation with body-z aligned to thrust and the given yaw."""
        zb = m.normalize(thrust_vec, np.array([0.0, 0.0, 1.0]))
        xc = np.array([np.cos(yaw), np.sin(yaw), 0.0])
        yb = m.normalize(np.cross(zb, xc), np.array([0.0, 1.0, 0.0]))
        xb = np.cross(yb, zb)
        R = np.column_stack([xb, yb, zb])
        return m.rotmat_to_quat(R)
