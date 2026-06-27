"""Shared types: rigid-body state, rider intent, control setpoints, mode enums."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from .math3d import quat_identity, quat_to_euler, vec3


@dataclass
class State:
    """Full rigid-body state, world (ENU) frame."""

    pos: np.ndarray = field(default_factory=lambda: vec3())   # m, world
    vel: np.ndarray = field(default_factory=lambda: vec3())   # m/s, world
    quat: np.ndarray = field(default_factory=quat_identity)   # body->world
    omega: np.ndarray = field(default_factory=lambda: vec3()) # rad/s, body
    t: float = 0.0                                            # sim time, s

    def copy(self) -> "State":
        return State(self.pos.copy(), self.vel.copy(),
                     self.quat.copy(), self.omega.copy(), self.t)

    @property
    def euler(self) -> np.ndarray:
        return quat_to_euler(self.quat)

    @property
    def altitude(self) -> float:
        return float(self.pos[2])

    @property
    def speed(self) -> float:
        return float(np.linalg.norm(self.vel))

    @property
    def ground_speed(self) -> float:
        return float(np.linalg.norm(self.vel[:2]))


@dataclass
class RiderIntent:
    """Normalized rider inputs. This is all the human is ever allowed to ask for;
    the controller interprets it, it never reaches the motors directly.

    Sticks centered == hold position + altitude (auto-hover).

      pitch [-1,1]  lean fwd(+)/back(-)  -> fwd/back velocity wish
      roll  [-1,1]  lean right(+)/left   -> right/left velocity wish
      yaw   [-1,1]  twist                -> yaw rate wish
      lift  [-1,1]  throttle up(+)/down  -> climb/descend rate wish
    """

    pitch: float = 0.0
    roll: float = 0.0
    yaw: float = 0.0
    lift: float = 0.0

    def clamped(self) -> "RiderIntent":
        c = lambda v: float(np.clip(v, -1.0, 1.0))  # noqa: E731
        return RiderIntent(c(self.pitch), c(self.roll), c(self.yaw), c(self.lift))


@dataclass
class Setpoint:
    """Control setpoint from the intent mapper / navigator.

    Only the fields relevant to the active control level get consumed; the
    position controller fills in the rest down the cascade.
    """

    # position / velocity targets (world ENU); None / NaN on an axis = no hold
    pos: np.ndarray | None = None
    vel_ff: np.ndarray = field(default_factory=lambda: vec3())   # m/s feedforward
    yaw: float | None = None                # rad; absolute heading hold
    yaw_rate_ff: float = 0.0                # rad/s feedforward


class FlightMode(str, Enum):
    """What the rider feels."""

    POSITION = "POSITION"   # full assist: neutral sticks => hold pos+alt
    ALTITUDE = "ALTITUDE"   # hold altitude, let it drift horizontally


class CommanderState(str, Enum):
    """Vehicle lifecycle. See safety.commander for the transition table."""

    INIT = "INIT"
    DISARMED = "DISARMED"
    ARMED = "ARMED"                    # motors live, on the ground, holding
    TAKEOFF = "TAKEOFF"
    FLYING = "FLYING"
    RETURN_TO_PIT = "RTP"              # battery/link failsafe -> fly home
    LANDING = "LANDING"
    # the "kill switch": a gentle synchronized descent, NOT a motor cut
    EMERGENCY_DESCENT = "EMERGENCY_DESCENT"


@dataclass
class FcOutput:
    """What the FC emits each tick."""

    fan_thrusts: np.ndarray             # N per fan, already saturated
    collective: float                   # N total commanded along body z
    torque_cmd: np.ndarray              # Nm body, commanded (pre-allocation)
    torque_actual: np.ndarray           # Nm body, after fan saturation
    mode: FlightMode
    state: CommanderState
    setpoint: Setpoint
    notes: tuple[str, ...] = ()         # human-readable events this tick
