"""The little dataclasses everything passes around: state, intent, setpoints, enums."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from .math3d import quat_identity, quat_to_euler, vec3


@dataclass
class State:
    """Complete rigid-body state, expressed in the world (ENU) frame."""

    pos: np.ndarray = field(default_factory=lambda: vec3())        # m, world
    vel: np.ndarray = field(default_factory=lambda: vec3())        # m/s, world
    quat: np.ndarray = field(default_factory=quat_identity)        # body->world
    omega: np.ndarray = field(default_factory=lambda: vec3())      # rad/s, body
    t: float = 0.0                                                 # sim clock, s

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
    """Normalized stick inputs -- the entire vocabulary the human gets.

    The FC reads these as *wishes* and figures out the motor commands itself;
    raw stick never touches a fan. Centered sticks mean "park here" (hover).

      pitch  [-1,1]  fwd(+)/back(-)    -> fwd/back velocity wish
      roll   [-1,1]  right(+)/left(-)  -> lateral velocity wish
      yaw    [-1,1]  twist             -> yaw *rate* wish
      lift   [-1,1]  up(+)/down(-)     -> climb/descend wish
    """

    pitch: float = 0.0
    roll: float = 0.0
    yaw: float = 0.0
    lift: float = 0.0

    def clamped(self) -> "RiderIntent":
        sat = lambda v: float(np.clip(v, -1.0, 1.0))  # noqa: E731
        return RiderIntent(sat(self.pitch), sat(self.roll), sat(self.yaw), sat(self.lift))


@dataclass
class Setpoint:
    """What the intent mapper / navigator hands down the cascade.

    Each control level only looks at the fields it cares about; the position
    loop backfills whatever's left as it goes.
    """

    # position / velocity targets, world ENU
    pos: np.ndarray | None = None           # m. None on an axis => don't hold it
    vel_ff: np.ndarray = field(default_factory=lambda: vec3())   # m/s feedforward
    yaw: float | None = None                # rad, absolute heading hold
    yaw_rate_ff: float = 0.0                # rad/s feedforward


class FlightMode(str, Enum):
    """What the flight feels like from the saddle."""

    POSITION = "POSITION"      # full assist; neutral sticks hold pos + alt
    ALTITUDE = "ALTITUDE"      # hold alt only, let it drift sideways (wind demo)


class CommanderState(str, Enum):
    """Vehicle lifecycle; the transition table lives in safety.commander."""

    INIT = "INIT"
    DISARMED = "DISARMED"
    ARMED = "ARMED"           # motors live, on ground, holding
    TAKEOFF = "TAKEOFF"
    FLYING = "FLYING"
    RETURN_TO_PIT = "RTP"     # battery / link failsafe -> fly home
    LANDING = "LANDING"
    EMERGENCY_DESCENT = "EMERGENCY_DESCENT"  # kill switch: gentle descent, not a power cut


@dataclass
class FcOutput:
    """One tick's worth of FC output."""

    fan_thrusts: np.ndarray                 # N per fan, post-saturation
    collective: float                       # N total along body z
    torque_cmd: np.ndarray                  # Nm body, what we asked for
    torque_actual: np.ndarray               # Nm body, what the fans could give
    mode: FlightMode
    state: CommanderState
    setpoint: Setpoint
    notes: tuple[str, ...] = ()             # readable events from this tick
