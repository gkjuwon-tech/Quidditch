"""A player flown by the real broom stack.

`BroomAgent` is a Player whose position is NOT scripted -- it comes from the
6-DOF broom plant driven by the full FlightController (commander + geofence +
fly-by-intent + the control cascade). A rider-AI turns a desired world velocity
into normalized stick intent (the inverse of the intent mapper), so a chase
goal flows: goal -> desired velocity -> RiderIntent -> FlightController ->
fan thrusts -> Dynamics -> new position.

It exposes the same surface the balls expect from a person (pos, vel, reach,
hand_toward, body_radius, id), so the no-contact ball avoidance and catch logic
work unchanged. Optionally flies on the onboard EKF (state_source="estimate").
"""

from __future__ import annotations

import numpy as np

from ..core import math3d as m
from ..core.params import Params
from ..core.types import CommanderState, RiderIntent, State
from ..estimation.eskf import EKF
from ..fc import FlightController
from ..safety.commander import Commands
from ..sim.dynamics import Dynamics
from ..sim.sensors import SensorSuite


def intent_for_velocity(state: State, v_des: np.ndarray, p: Params,
                        face_travel: bool = False) -> RiderIntent:
    """Inverse of the intent mapper: desired WORLD velocity -> stick intent."""
    yaw = m.yaw_of(state.quat)
    c, s = np.cos(yaw), np.sin(yaw)
    vx, vy, vz = v_des
    # body-frame decomposition (mapper uses [vx;vy] = R[fwd;right], R^-1 = R)
    fwd = c * vx + s * vy
    right = s * vx - c * vy
    pitch = np.clip(fwd / p.max_speed_xy, -1.0, 1.0)
    roll = np.clip(right / p.max_speed_xy, -1.0, 1.0)
    lift = np.clip(vz / p.max_climb_rate, -1.0, 1.0)
    yaw_cmd = 0.0
    if face_travel and np.hypot(vx, vy) > 1.0:
        desired_yaw = np.arctan2(vy, vx)
        err = (desired_yaw - yaw + np.pi) % (2 * np.pi) - np.pi
        yaw_cmd = float(np.clip(err * 1.5, -1.0, 1.0))
    return RiderIntent(pitch=float(pitch), roll=float(roll),
                       yaw=yaw_cmd, lift=float(lift))


class BroomAgent:
    def __init__(self, pid: int, pos, rider_ai, *, params: Params | None = None,
                 reach: float = 1.2, body_radius: float = 0.4,
                 state_source: str = "truth", ekf_div: int = 4, seed: int = 0):
        self.id = pid
        self.p = params or Params()
        self.rider_ai = rider_ai             # callable(world, self) -> v_des (world)
        self.reach = reach
        self.body_radius = body_radius
        self.state_source = state_source
        self.tagged_out = False
        self._penalty_until = 0.0

        self.dyn = Dynamics(self.p, State(pos=np.asarray(pos, float)))
        self.fc = FlightController(self.p)
        self._spawn_flying()

        if state_source == "estimate":
            self.sensors = SensorSuite(self.p, seed=seed)
            self.est = EKF(self.p, self.dyn.state)
            self.ekf_div = max(1, ekf_div)   # run the 15-state EKF at 400/ekf_div Hz
            self._ekf_tick = 0
            self._imu_accum: list = []
        else:
            self.sensors = self.est = None

    # ------------------------------------------------------------------ #
    def _spawn_flying(self) -> None:
        """Pre-spin the rotors to hover and hand control straight to the rider."""
        self.dyn.fan_thrust[:] = self.p.hover_thrust / self.p.num_fans
        self.fc.commander.state = CommanderState.FLYING
        self.fc.mapper.reset(self.dyn.state)
        self.fc._was_manual = True

    # ----- Player-compatible surface ---------------------------------- #
    @property
    def pos(self) -> np.ndarray:
        return self.dyn.state.pos

    @property
    def vel(self) -> np.ndarray:
        return self.dyn.state.vel

    def hand_toward(self, target: np.ndarray) -> np.ndarray:
        d = np.asarray(target, float) - self.pos
        n = float(np.linalg.norm(d))
        return self.pos.copy() if n < 1e-6 else self.pos + (d / n) * self.reach

    # ----- stepped by the World/match each tick ----------------------- #
    def act(self, world, dt: float, vel_override: np.ndarray | None = None) -> None:
        if vel_override is not None:
            # The referee (Dementor) owns the velocity: it already folded in
            # any penalty state and inter-broom deconfliction.
            v_des = np.asarray(vel_override, float)
        elif self.tagged_out and world.t < self._penalty_until:
            v_des = np.array([0.0, 0.0, -0.3])   # penalised: drift down, idle
        else:
            self.tagged_out = False
            v_des = self.rider_ai(world, self)
        v_des = m.clamp_norm(np.asarray(v_des, float), self.p.max_speed_xy)

        intent = intent_for_velocity(self.dyn.state, v_des, self.p)

        if self.state_source == "estimate":
            # Read the IMU every tick (cheap; the rate loop needs fresh gyro),
            # but run the heavy 15-state EKF predict/fuse only every ekf_div
            # ticks -- fast inner control on a 100 Hz estimate.
            gyro, accel = self.sensors.imu(self.dyn.state, self.dyn.accel_world)
            self._imu_accum.append((gyro, accel))
            est = self.est.state
            est.omega = gyro - self.est.gyro_bias
            state_for_fc = est
        else:
            state_for_fc = self.dyn.state

        out = self.fc.update(intent, state_for_fc, 1.0, True, Commands(), dt)
        self.dyn.step(out.fan_thrusts, dt)

        if self.state_source == "estimate":
            self._ekf_tick += 1
            if self._ekf_tick % self.ekf_div == 0:
                g = np.mean([s[0] for s in self._imu_accum], axis=0)
                a = np.mean([s[1] for s in self._imu_accum], axis=0)
                self._imu_accum.clear()
                self.est.predict(g, a, dt * self.ekf_div)
                self.est.fuse_mag(self.sensors.mag(self.dyn.state))
                gp, gv = self.sensors.gnss(self.dyn.state)
                self.est.fuse_gnss(gp, gv, dt * self.ekf_div)

    def penalise(self, until: float) -> None:
        self.tagged_out = True
        self._penalty_until = until
