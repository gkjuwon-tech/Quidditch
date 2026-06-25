"""Shared data types: rigid-body state, rider intent, control setpoints, mode enums."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from .math3d import quat_identity, quat_to_euler, vec3


@dataclass
class State:
    """Full rigid-body state in the world (ENU) frame."""

    pos: np.ndarray = field(default_factory=lambda: vec3())        # m, world
    vel: np.ndarray = field(default_factory=lambda: vec3())        # m/s, world
    quat: np.ndarray = field(default_factory=quat_identity)        # body->world
    omega: np.ndarray = field(default_factory=lambda: vec3())      # rad/s, body
    t: float = 0.0                                                 # sim time, s

    def copy(self) -> "State":
        return State(self.pos.copy(), self.vel.copy(),
                     self.quat.copy(), self.omega.copy(), self.t)

    @property
    def euler(self) -> np.ndarray:
        """[roll, pitch, yaw] in radians."""
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
    """Normalized rider inputs. This is ALL the human is allowed to ask for.

    The flight controller interprets intent; it never passes raw commands to
    the motors. Sticks centered == "hold position and altitude" (auto-hover).

      pitch:  [-1, 1]  lean forward(+)/back(-)  -> forward/back velocity wish
      roll:   [-1, 1]  lean right(+)/left(-)    -> right/left velocity wish
      yaw:    [-1, 1]  twist                    -> yaw RATE wish (heading change)
      lift:   [-1, 1]  throttle up(+)/down(-)   -> climb/descend rate wish
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
    """Control setpoints produced by the intent mapper / navigator.

    Only the fields relevant to the active control level are consumed. The
    position controller fills in the rest down the cascade.
    """

    # Position / velocity targets (world ENU)
    pos: np.ndarray | None = None           # m; None => no position hold on that axis
    vel_ff: np.ndarray = field(default_factory=lambda: vec3())   # m/s feedforward
    yaw: float | None = None                # rad; absolute heading hold
    yaw_rate_ff: float = 0.0                # rad/s feedforward


class FlightMode(str, Enum):
    """High-level flight mode (what the rider experiences)."""

    POSITION = "POSITION"      # full assist: neutral sticks => hold pos+alt
    ALTITUDE = "ALTITUDE"      # hold altitude, free horizontal drift (windy demo)


class CommanderState(str, Enum):
    """Vehicle lifecycle. See safety.commander for the transition table."""

    INIT = "INIT"
    DISARMED = "DISARMED"
    ARMED = "ARMED"           # motors live, on ground, holding
    TAKEOFF = "TAKEOFF"
    FLYING = "FLYING"
    RETURN_TO_PIT = "RTP"     # battery / link failsafe -> fly home
    LANDING = "LANDING"
    EMERGENCY_DESCENT = "EMERGENCY_DESCENT"  # the "kill switch": gentle, NOT a cut


@dataclass
class FcOutput:
    """What the flight controller emits each tick."""

    fan_thrusts: np.ndarray                 # N per fan, already saturated
    collective: float                       # N total commanded along body z
    torque_cmd: np.ndarray                  # Nm body, commanded (pre-allocation)
    torque_actual: np.ndarray               # Nm body, after fan saturation
    mode: FlightMode
    state: CommanderState
    setpoint: Setpoint
    notes: tuple[str, ...] = ()             # human-readable events this tick
