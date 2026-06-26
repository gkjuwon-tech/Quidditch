"""Central parameter store for the NIMBUS broom eVTOL.

One dataclass, grouped by subsystem. Every magic number in the stack lives
here so tuning never means hunting through modules (lesson stolen from PX4's
parameter system, minus the 1500-parameter sprawl).

Units: SI throughout (m, kg, s, N, Nm, rad).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .math3d import GRAVITY


def _default_fan_layout() -> np.ndarray:
    """8 ducted fans on short outriggers along a 2.4 m broom body.

    Columns: [x, y, z, spin]. x=forward, y=left, z=up (body frame).
    Lateral y-offset gives roll authority; x-spread gives pitch authority;
    alternating spin directions give yaw authority. Full-rank 4x8 allocation.
    """
    # tail (bristles) is wider for stability, like a real broom flare.
    return np.array([
        [+0.90, +0.22, -0.05, +1.0],
        [+0.90, -0.22, -0.05, -1.0],
        [+0.30, +0.24, -0.05, -1.0],
        [+0.30, -0.24, -0.05, +1.0],
        [-0.30, +0.24, -0.05, +1.0],
        [-0.30, -0.24, -0.05, -1.0],
        [-0.90, +0.26, -0.05, -1.0],
        [-0.90, -0.26, -0.05, +1.0],
    ])


@dataclass
class Params:
    # ------------------------------------------------------------------ #
    # Loop timing
    # ------------------------------------------------------------------ #
    dt: float = 0.0025                 # 400 Hz inner loop
    pos_loop_div: int = 4              # run position loop at 400/4 = 100 Hz

    # ------------------------------------------------------------------ #
    # Mass / inertia  (rider ~80 kg + vehicle ~40 kg)
    # ------------------------------------------------------------------ #
    mass: float = 120.0
    # Long thin body: low roll inertia, high pitch/yaw inertia.
    inertia_diag: np.ndarray = field(
        default_factory=lambda: np.array([8.0, 60.0, 60.0]))
    cg_offset: np.ndarray = field(default_factory=lambda: np.zeros(3))

    # ------------------------------------------------------------------ #
    # Propulsion (ducted electric fans)
    # ------------------------------------------------------------------ #
    fan_layout: np.ndarray = field(default_factory=_default_fan_layout)
    fan_thrust_max: float = 360.0      # N per fan (cluster T/W ~ 2.4)
    fan_thrust_min: float = 0.0        # fans cannot pull (single direction)
    fan_yaw_coeff: float = 0.06        # reaction torque per N of fan thrust
    fan_tau: float = 0.04              # 1st-order thrust response time const, s

    # ------------------------------------------------------------------ #
    # Aerodynamics (simple)
    # ------------------------------------------------------------------ #
    drag_lin: float = 0.8              # translational quadratic drag coeff
    drag_rot: float = 6.0             # rotational linear damping coeff

    # ------------------------------------------------------------------ #
    # Rider envelope (fly-by-intent limits) -- the heart of "you can't crash"
    # ------------------------------------------------------------------ #
    max_speed_xy: float = 16.0         # m/s (~58 km/h match speed cap)
    max_climb_rate: float = 4.0        # m/s up
    max_descent_rate: float = 3.0      # m/s down
    max_yaw_rate: float = np.deg2rad(90.0)
    max_tilt: float = np.deg2rad(35.0)  # never let the human bank past this

    # ------------------------------------------------------------------ #
    # Position / velocity controller
    # ------------------------------------------------------------------ #
    kp_pos_xy: float = 0.7
    kp_pos_z: float = 1.3
    # Velocity-loop P sits well below the tilt bandwidth, with strong D
    # damping -- this is what kills the attitude limit cycle on a heavy,
    # tilt-to-translate vehicle. Tuned in SITL (see scenarios/tune notes).
    kp_vel_xy: float = 2.0
    ki_vel_xy: float = 0.4              # wind/disturbance rejection (no limit cycle)
    kd_vel_xy: float = 1.0
    kp_vel_z: float = 6.0
    ki_vel_z: float = 3.0
    kd_vel_z: float = 0.2
    vel_i_limit: float = 6.0           # m/s^2 anti-windup clamp on velocity I-term
    max_accel_xy: float = 5.0          # m/s^2 commanded accel clamp (~27 deg tilt)

    # ------------------------------------------------------------------ #
    # Attitude controller (P on quaternion error -> rate setpoint)
    # Gains kept gentle: a 120 kg vehicle with ~60 kg.m^2 pitch/yaw inertia
    # cannot honor aggressive rate demands without saturating the fans.
    # ------------------------------------------------------------------ #
    kp_att_rp: float = 6.0             # roll/pitch -- fast tilt so the velocity
    kp_att_yaw: float = 2.5            #              loop has bandwidth to spare
    att_rate_limit_rp: float = np.deg2rad(150.0)

    # ------------------------------------------------------------------ #
    # Rate controller (PID -> body torque). Sized to stay within the fan
    # cluster's torque capacity (~860 Nm pitch/yaw) across normal demands.
    # ------------------------------------------------------------------ #
    kp_rate: np.ndarray = field(
        default_factory=lambda: np.array([40.0, 200.0, 200.0]))
    ki_rate: np.ndarray = field(
        default_factory=lambda: np.array([12.0, 50.0, 50.0]))
    kd_rate: np.ndarray = field(
        default_factory=lambda: np.array([1.0, 5.0, 5.0]))
    rate_i_limit: np.ndarray = field(
        default_factory=lambda: np.array([30.0, 150.0, 150.0]))

    # ------------------------------------------------------------------ #
    # Geofence (the invisible rubber walls of the pitch)
    # ------------------------------------------------------------------ #
    fence_ceiling: float = 150.0       # m, soft ceiling -- real, vertical Quidditch
                                       # (hardware/analysis/altitude_ceiling.py: thrust
                                       # margin holds to km; chute survivable from here)
    fence_floor: float = 3.0           # m, soft floor (never auto below this in flight)
    fence_margin: float = 4.0          # m, braking buffer before a hard limit
    # Lateral fence: convex polygon (CCW) in world XY. Default = 100x50 pitch.
    fence_polygon: np.ndarray = field(default_factory=lambda: np.array([
        [-50.0, -25.0], [50.0, -25.0], [50.0, 25.0], [-50.0, 25.0],
    ]))

    # ------------------------------------------------------------------ #
    # Battery / failsafe
    # ------------------------------------------------------------------ #
    batt_capacity_wh: float = 2600.0   # usable energy
    batt_hover_eta: float = 0.62       # electrical->aero efficiency at hover
    batt_rtp_soc: float = 0.30         # below this -> Return To Pit
    batt_land_soc: float = 0.15        # below this -> force land now
    # Pit sits inside the geofence keep-in box (not out at the hard wall).
    pit_location: np.ndarray = field(default_factory=lambda: np.array([-38.0, 0.0]))
    pit_approach_alt: float = 8.0      # m, cruise home altitude

    # ------------------------------------------------------------------ #
    # Takeoff / landing
    # ------------------------------------------------------------------ #
    takeoff_alt: float = 6.0
    takeoff_speed: float = 1.5
    land_speed: float = 0.8
    landed_alt: float = 0.15
    emergency_descent_speed: float = 1.2  # the gentle "kill" descent rate

    def __post_init__(self) -> None:
        # Defensive: make sure arrays are float ndarrays (callers may pass lists).
        self.inertia_diag = np.asarray(self.inertia_diag, dtype=float)
        self.fan_layout = np.asarray(self.fan_layout, dtype=float)
        self.fence_polygon = np.asarray(self.fence_polygon, dtype=float)

    @property
    def hover_thrust(self) -> float:
        return self.mass * GRAVITY

    @property
    def num_fans(self) -> int:
        return self.fan_layout.shape[0]
