"""Simulator: closes the loop between the FlightController and the plant.

state_source:
  "truth"    - controller flies on ground-truth state (standard SITL; the
               headline scenarios use this to isolate guidance/control/safety).
  "estimate" - controller flies on the onboard estimate from synthetic noisy
               IMU + GNSS (experimental end-to-end realism).
"""

from __future__ import annotations

import numpy as np

from ..core.params import Params
from ..core.types import FlightMode, RiderIntent, State
from ..fc import FlightController
from ..estimation.eskf import EKF
from ..estimation.estimator import Estimator
from ..safety.commander import Commands
from ..telemetry.logger import TelemetryLog
from .battery import Battery
from .dynamics import Dynamics
from .sensors import SensorSuite


class Simulator:
    def __init__(self, params: Params | None = None, *,
                 initial: State | None = None,
                 mode: FlightMode = FlightMode.POSITION,
                 state_source: str = "truth",
                 initial_soc: float = 1.0,
                 gnss_div: int = 8,
                 backend: str = "python",
                 wind=None,
                 estimator: str = "ekf",
                 seed: int = 0):
        self.p = params or Params()
        self.state_source = state_source
        self.gnss_div = gnss_div
        init = initial or State(pos=np.array([self.p.pit_location[0],
                                              self.p.pit_location[1], 0.0]))
        self.dyn = Dynamics(self.p, init, wind=wind)
        self.batt = Battery(self.p, initial_soc)
        self.fc = FlightController(self.p, mode=mode, backend=backend)
        self.log = TelemetryLog()
        self._tick = 0

        if state_source == "estimate":
            self.sensors = SensorSuite(self.p, seed=seed)
            self.estimator = (EKF(self.p, init) if estimator == "ekf"
                              else Estimator(self.p, init))
        else:
            self.sensors = self.estimator = None

    def step(self, intent: RiderIntent, cmd: Commands, link_ok: bool = True):
        p, dt = self.p, self.p.dt

        if self.state_source == "estimate":
            gyro, accel = self.sensors.imu(self.dyn.state, self.dyn.accel_world)
            est = self.estimator.state
            est.omega = gyro - self.estimator.gyro_bias
            state_for_fc = est
        else:
            state_for_fc = self.dyn.state

        out = self.fc.update(intent, state_for_fc, self.batt.soc, link_ok, cmd, dt)
        self.dyn.step(out.fan_thrusts, dt)

        if self.state_source == "estimate":
            self.estimator.predict(gyro, accel, dt)
            if hasattr(self.estimator, "fuse_mag"):
                self.estimator.fuse_mag(self.sensors.mag(self.dyn.state))
            if self._tick % self.gnss_div == 0:
                gp, gv = self.sensors.gnss(self.dyn.state)
                self.estimator.fuse_gnss(gp, gv, dt * self.gnss_div)

        self.batt.update(self.dyn.total_thrust, dt)
        self._record(out)
        self._tick += 1
        return out

    def run(self, duration: float, controller):
        """controller(t, sim) -> (RiderIntent, Commands, link_ok)."""
        n = int(duration / self.p.dt)
        for _ in range(n):
            t = self.dyn.state.t
            intent, cmd, link_ok = controller(t, self)
            self.step(intent, cmd, link_ok)
        return self.log

    def _record(self, out) -> None:
        s = self.dyn.state
        eul = np.rad2deg(s.euler)
        self.log.append(
            t=s.t, x=float(s.pos[0]), y=float(s.pos[1]), z=float(s.pos[2]),
            vx=float(s.vel[0]), vy=float(s.vel[1]), vz=float(s.vel[2]),
            speed=s.speed, roll=float(eul[0]), pitch=float(eul[1]),
            yaw=float(eul[2]), soc=self.batt.soc * 100.0,
            thrust=self.dyn.total_thrust, state=out.state.value,
        )
