"""Flight controller composition for the NIMBUS broom.

The commander owns lifecycle + failsafe decisions. manual flight is translated
through the intent mapper, then the geofence clamps the resulting setpoint
before the position/attitude/rate cascade allocates fan thrust. integrators are
reset at control-authority boundaries so a manual hold doesn't bias autonomous
return or landing.
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
        # inner cascade (position->attitude->rate->mixer) is a swappable
        # backend: "python" for dev, "rust" for the real-time core.
        self.core = make_backend(self.p, backend)
        self.mapper = IntentMapper(self.p)
        self.geofence = Geofence(self.p)
        self.commander = Commander(self.p)
        self._was_manual = False

    def update(self, intent: RiderIntent, state: State, soc: float,
               link_ok: bool, cmd: Commands, dt: float) -> FcOutput:
        p = self.p
        notes: list[str] = []

        # commander returns a nav setpoint when it owns the aircraft
        nav_sp = self.commander.update(state, soc, link_ok, cmd, dt)
        notes.extend(self.commander.notes)

        # reset only on authority changes. steady manual-flight integrator
        # state is left intact until the commander takes over for nav or
        # failsafe work.
        if self.commander.is_manual and not self._was_manual:
            self.mapper.reset(state)
        elif not self.commander.is_manual and self._was_manual:
            self.core.reset()
        self._was_manual = self.commander.is_manual

        # disarmed => no latent controller state and no thrust
        if not self.commander.motors_armed:
            self.core.reset()
            zeros = np.zeros(p.num_fans)
            return FcOutput(zeros, 0.0, np.zeros(3), np.zeros(3),
                            self.mode, self.commander.state,
                            Setpoint(), tuple(notes))

        # manual flight uses stick intent; nav states use the commander setpoint
        if self.commander.is_manual:
            sp = self.mapper.update(intent, state, dt, self.mode)
        else:
            sp = nav_sp if nav_sp is not None else Setpoint(pos=state.pos.copy())

        # apply the geofence last so it protects both rider and autonomous sps
        allow_ground = self.commander.state in (
            CommanderState.LANDING, CommanderState.EMERGENCY_DESCENT)
        sp, breaching = self.geofence.apply(state, sp, allow_ground=allow_ground)
        if breaching:
            notes.append("geofence: pushing back from boundary")

        # inner cascade returns per-fan thrust commands
        fan, collective, torque, actual = self.core.control(state, sp, dt)

        return FcOutput(fan, collective, torque, actual,
                        self.mode, self.commander.state, sp, tuple(notes))

    @property
    def state(self) -> CommanderState:
        return self.commander.state
