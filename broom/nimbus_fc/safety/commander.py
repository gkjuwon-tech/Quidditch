"""Commander: the vehicle lifecycle state machine (PX4 'commander' analogue).

Owns the transitions between DISARMED / ARMED / TAKEOFF / FLYING /
RETURN_TO_PIT / LANDING / EMERGENCY_DESCENT, and -- crucially -- generates the
control setpoint for every NON-manual state. In FLYING it returns None to mean
"hand the setpoint to the rider (fly-by-intent)".

Two design choices worth calling out:
  * The "kill switch" is EMERGENCY_DESCENT: a gentle, controlled, synchronized
    descent -- NOT a motor cut. Cutting motors on a manned vehicle is how you
    turn a software fault into a funeral. The estop makes the broom sink
    softly and park on the ground.
  * Failsafes can fire from any flying state and always win over rider intent.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..core import math3d as m
from ..core.params import Params
from ..core.types import CommanderState, Setpoint, State
from .failsafe import Failsafe, FailsafeAction


@dataclass
class Commands:
    """Edge-triggered pilot/ground commands for this tick."""
    arm: bool = False
    takeoff: bool = False
    kill: bool = False        # the big red button (-> gentle emergency descent)
    disarm: bool = False


class Commander:
    def __init__(self, params: Params):
        self.p = params
        self.state = CommanderState.DISARMED
        self.failsafe = Failsafe(params)
        self._hold_xy = np.zeros(2)     # latched target for nav states
        self._hold_yaw = 0.0
        self.notes: tuple[str, ...] = ()

    @property
    def motors_armed(self) -> bool:
        return self.state not in (CommanderState.INIT, CommanderState.DISARMED)

    @property
    def is_manual(self) -> bool:
        return self.state == CommanderState.FLYING

    # ------------------------------------------------------------------ #
    def update(self, state: State, soc: float, link_ok: bool,
               cmd: Commands, dt: float) -> Setpoint | None:
        """Advance the state machine. Returns a nav Setpoint, or None for manual."""
        notes: list[str] = []
        action, msg = self.failsafe.evaluate(soc, link_ok, dt)

        # --- highest priority: the kill switch --------------------------
        if cmd.kill and self.motors_armed and self.state != CommanderState.EMERGENCY_DESCENT:
            self._enter(CommanderState.EMERGENCY_DESCENT, state, notes,
                        "KILL: emergency controlled descent")

        # --- failsafes (override rider, from any flying state) ----------
        elif self._airborne():
            if action == FailsafeAction.LAND_NOW and self.state != CommanderState.LANDING:
                self._enter(CommanderState.LANDING, state, notes, msg)
            elif (action == FailsafeAction.RETURN_TO_PIT
                  and self.state not in (CommanderState.RETURN_TO_PIT, CommanderState.LANDING)):
                self._enter(CommanderState.RETURN_TO_PIT, state, notes, msg)

        # --- normal lifecycle commands ----------------------------------
        if self.state == CommanderState.DISARMED and cmd.arm:
            self._enter(CommanderState.ARMED, state, notes, "armed")
        elif self.state == CommanderState.ARMED:
            if cmd.disarm:
                self._enter(CommanderState.DISARMED, state, notes, "disarmed")
            elif cmd.takeoff:
                self._enter(CommanderState.TAKEOFF, state, notes, "takeoff")

        sp = self._run_state(state, notes)
        self.notes = tuple(notes)
        return sp

    # ------------------------------------------------------------------ #
    def _run_state(self, state: State, notes: list[str]) -> Setpoint | None:
        p = self.p
        s = self.state

        if s in (CommanderState.DISARMED, CommanderState.INIT):
            return Setpoint(pos=np.array([state.pos[0], state.pos[1], 0.0]))

        if s == CommanderState.ARMED:
            # Hold on the ground, motors live, waiting for takeoff.
            return Setpoint(pos=np.array([self._hold_xy[0], self._hold_xy[1], 0.0]),
                            yaw=self._hold_yaw)

        if s == CommanderState.TAKEOFF:
            sp = Setpoint(pos=np.array([self._hold_xy[0], self._hold_xy[1],
                                        p.takeoff_alt]), yaw=self._hold_yaw)
            if abs(state.pos[2] - p.takeoff_alt) < 0.5:
                self._enter(CommanderState.FLYING, state, notes, "in flight - rider has control")
            return sp

        if s == CommanderState.FLYING:
            return None  # rider has control via the intent mapper

        if s == CommanderState.RETURN_TO_PIT:
            pit = p.pit_location
            sp = Setpoint(pos=np.array([pit[0], pit[1], p.pit_approach_alt]),
                          yaw=self._hold_yaw)
            if np.linalg.norm(state.pos[:2] - pit) < 1.5:
                self._enter(CommanderState.LANDING, state, notes, "over pit - landing")
            return sp

        if s == CommanderState.LANDING:
            # Descend in place to the ground at the gentle land speed.
            sp = Setpoint(pos=np.array([state.pos[0], state.pos[1], np.nan]),
                          vel_ff=np.array([0.0, 0.0, -p.land_speed]),
                          yaw=self._hold_yaw)
            self._maybe_landed(state, notes)
            return sp

        if s == CommanderState.EMERGENCY_DESCENT:
            sp = Setpoint(pos=np.array([state.pos[0], state.pos[1], np.nan]),
                          vel_ff=np.array([0.0, 0.0, -p.emergency_descent_speed]),
                          yaw=self._hold_yaw)
            self._maybe_landed(state, notes)
            return sp

        return None

    # ------------------------------------------------------------------ #
    def _enter(self, new: CommanderState, state: State, notes: list[str], msg: str) -> None:
        self._hold_xy = state.pos[:2].copy()
        self._hold_yaw = m.yaw_of(state.quat)
        self.state = new
        notes.append(msg)

    def _airborne(self) -> bool:
        return self.state in (CommanderState.TAKEOFF, CommanderState.FLYING,
                              CommanderState.RETURN_TO_PIT)

    def _maybe_landed(self, state: State, notes: list[str]) -> None:
        if state.pos[2] <= self.p.landed_alt and abs(state.vel[2]) < 0.3:
            self._enter(CommanderState.DISARMED, state, notes, "landed and disarmed")
