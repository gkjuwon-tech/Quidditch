"""FlightController: the whole brain, wired together.

Pipeline per tick (this ordering is the safety story):

    rider intent ─┐
                  ├─► COMMANDER ─► nav setpoint (or "manual")
    failsafes ────┘                     │
                                        ▼
                       manual? ─► INTENT MAPPER (fly-by-intent)
                                        │
                                        ▼
                                   GEOFENCE  (clamp + rubber walls)
                                        │
                                        ▼
                    POSITION ─► ATTITUDE ─► RATE ─► MIXER ─► fan thrusts

Safety layers compose: the commander can seize control from the rider, and the
geofence then constrains whatever setpoint survives -- so neither a panicking
rider nor a failsafe can drive the broom out of the volume or into the ground
hard. Disarmed => fans commanded to zero and every integrator reset.
"""

from __future__ import annotations

import numpy as np

from .control.attitude import AttitudeController
from .control.mixer import Mixer
from .control.position import PositionController
from .control.rate import RateController
from .core.params import Params
from .core.types import (
    CommanderState,
    FcOutput,
    FlightMode,
    RiderIntent,
    Setpoint,
    State,
)
from .intent.mapper import IntentMapper
from .safety.commander import Commander, Commands
from .safety.geofence import Geofence


class FlightController:
    def __init__(self, params: Params | None = None,
                 mode: FlightMode = FlightMode.POSITION):
        self.p = params or Params()
        self.mode = mode
        self.mixer = Mixer(self.p)
        self.position = PositionController(self.p)
        self.attitude = AttitudeController(self.p)
        self.rate = RateController(self.p)
        self.mapper = IntentMapper(self.p)
        self.geofence = Geofence(self.p)
        self.commander = Commander(self.p)

        self._tick = 0
        self._was_manual = False
        # Cached outer-loop outputs (position loop runs slower than the inner loop)
        self._collective = self.p.hover_thrust
        self._q_des = np.array([1.0, 0.0, 0.0, 0.0])
        self._yaw_rate_ff = 0.0

    # ------------------------------------------------------------------ #
    def update(self, intent: RiderIntent, state: State, soc: float,
               link_ok: bool, cmd: Commands, dt: float) -> FcOutput:
        p = self.p
        notes: list[str] = []

        # 1) Commander: lifecycle + failsafes. Returns nav setpoint or None.
        nav_sp = self.commander.update(state, soc, link_ok, cmd, dt)
        notes.extend(self.commander.notes)

        # Smooth handoff: latch the intent mapper to current state when the
        # rider (re)gains control.
        if self.commander.is_manual and not self._was_manual:
            self.mapper.reset(state)
        self._was_manual = self.commander.is_manual

        # 2) Disarmed: motors off, reset integrators, bail early.
        if not self.commander.motors_armed:
            self._reset_integrators()
            zeros = np.zeros(p.num_fans)
            return FcOutput(zeros, 0.0, np.zeros(3), np.zeros(3),
                            self.mode, self.commander.state,
                            Setpoint(), tuple(notes))

        # 3) Setpoint source: rider (manual) or commander (nav).
        if self.commander.is_manual:
            sp = self.mapper.update(intent, state, dt, self.mode)
        else:
            sp = nav_sp if nav_sp is not None else Setpoint(pos=state.pos.copy())

        # 4) Geofence guard (every state). The in-flight floor yields during
        #    landing / emergency descent so the broom can reach the ground.
        allow_ground = self.commander.state in (
            CommanderState.LANDING, CommanderState.EMERGENCY_DESCENT)
        sp, breaching = self.geofence.apply(state, sp, allow_ground=allow_ground)
        if breaching:
            notes.append("geofence: pushing back from boundary")

        # 5) Outer loop (position) at the reduced rate; inner loops every tick.
        if self._tick % p.pos_loop_div == 0:
            self._collective, self._q_des, self._yaw_rate_ff = \
                self.position.update(sp, state, dt * p.pos_loop_div)
        self._tick += 1

        rate_sp = self.attitude.update(state.quat, self._q_des, self._yaw_rate_ff)
        torque = self.rate.update(rate_sp, state.omega, dt)
        fan, actual = self.mixer.allocate(self._collective, torque)

        return FcOutput(fan, self._collective, torque, actual,
                        self.mode, self.commander.state, sp, tuple(notes))

    # ------------------------------------------------------------------ #
    def _reset_integrators(self) -> None:
        self.position.reset()
        self.rate.reset()
        self._collective = self.p.hover_thrust
        self._q_des = np.array([1.0, 0.0, 0.0, 0.0])
        self._yaw_rate_ff = 0.0

    @property
    def state(self) -> CommanderState:
        return self.commander.state
