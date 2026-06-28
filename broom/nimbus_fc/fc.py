"""Where the NIMBUS flight controller is bolted together.

The commander calls lifecycle and failsafe. Manual flight goes through the
intent mapper, the geofence then clamps whatever setpoint comes out, and only
then does the position/attitude/rate cascade hand thrust to the fans.
Integrators get reset whenever control authority changes hands, so a long
manual hold can't bias a later autonomous return or landing.
"""

from __future__ import annotations

import numpy as np

from .control.backend import make_backend
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
                 mode: FlightMode = FlightMode.POSITION,
                 backend: str = "python"):
        self.p = params or Params()
        self.mode = mode
        # the inner cascade (position->attitude->rate->mixer) is swappable:
        # "python" for dev work, "rust" for the real-time core
        self.core = make_backend(self.p, backend)
        self.mapper = IntentMapper(self.p)
        self.geofence = Geofence(self.p)
        self.commander = Commander(self.p)
        self._was_manual = False

    def update(self, intent: RiderIntent, state: State, soc: float,
               link_ok: bool, cmd: Commands, dt: float) -> FcOutput:
        p = self.p
        notes: list[str] = []

        # when the commander owns the aircraft it hands back a nav setpoint
        nav_sp = self.commander.update(state, soc, link_ok, cmd, dt)
        notes.extend(self.commander.notes)

        # only reset on a hand-off. steady manual integrator state is left
        # alone until the commander steps in for nav or a failsafe.
        if self.commander.is_manual and not self._was_manual:
            self.mapper.reset(state)
        elif not self.commander.is_manual and self._was_manual:
            self.core.reset()
        self._was_manual = self.commander.is_manual

        # disarmed: drop any latent controller state, command zero thrust
        if not self.commander.motors_armed:
            self.core.reset()
            zeros = np.zeros(p.num_fans)
            return FcOutput(zeros, 0.0, np.zeros(3), np.zeros(3),
                            self.mode, self.commander.state,
                            Setpoint(), tuple(notes))

        # manual flight rides stick intent; nav states ride the commander setpoint
        if self.commander.is_manual:
            sp = self.mapper.update(intent, state, dt, self.mode)
        else:
            sp = nav_sp if nav_sp is not None else Setpoint(pos=state.pos.copy())

        # geofence goes last, so it guards rider and autonomous setpoints alike
        allow_ground = self.commander.state in (
            CommanderState.LANDING, CommanderState.EMERGENCY_DESCENT)
        sp, breaching = self.geofence.apply(state, sp, allow_ground=allow_ground)
        if breaching:
            notes.append("geofence: pushing back from boundary")

        # cascade spits out a thrust command per fan
        fan, collective, torque, actual = self.core.control(state, sp, dt)

        return FcOutput(fan, collective, torque, actual,
                        self.mode, self.commander.state, sp, tuple(notes))

    @property
    def state(self) -> CommanderState:
        return self.commander.state
