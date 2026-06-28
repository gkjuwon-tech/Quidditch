"""All the tunables in one place.

Every magic number lives in this dataclass, grouped by subsystem, so tuning
is a one-file job instead of a grep safari. Think PX4 params without the
1500-knob sprawl.

Everything is SI (m, kg, s, N, Nm, rad).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .math3d import GRAVITY


def _default_fan_layout() -> np.ndarray:
    """Eight ducted fans on stubby outriggers down a 2.4 m broom.

    Rows are [x, y, z, spin] in the body frame (x fwd, y left, z up). The
    y-offset buys roll, the x-spread buys pitch, and the alternating spins
    buy yaw -- so the 4x8 allocation comes out full rank.
    """
    # bristle end flares a touch wider, same reason a real broom does
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
    # loop timing
    dt: float = 0.0025                 # inner loop, 400 Hz
    pos_loop_div: int = 4              # position loop every 4th tick -> 100 Hz

    # mass / inertia (roughly 80 kg rider + 40 kg airframe)
    mass: float = 120.0
    # long skinny body => cheap to roll, expensive to pitch/yaw
    inertia_diag: np.ndarray = field(
        default_factory=lambda: np.array([8.0, 60.0, 60.0]))
    cg_offset: np.ndarray = field(default_factory=lambda: np.zeros(3))

    # propulsion: ducted electric fans
    fan_layout: np.ndarray = field(default_factory=_default_fan_layout)
    fan_thrust_max: float = 360.0      # N per fan, gives cluster T/W ~ 2.4
    fan_thrust_min: float = 0.0        # one-way fans, no reverse pull
    fan_yaw_coeff: float = 0.06        # reaction torque per N
    fan_tau: float = 0.04              # thrust 1st-order lag (s)

    # crude aero
    drag_lin: float = 0.8              # quadratic translational drag
    drag_rot: float = 6.0              # linear rotational damping

    # rider envelope -- this is the whole "can't crash by flying badly" idea
    max_speed_xy: float = 16.0         # m/s, ~58 km/h match cap
    max_climb_rate: float = 4.0        # m/s up
    max_descent_rate: float = 3.0      # m/s down
    max_yaw_rate: float = np.deg2rad(90.0)
    max_tilt: float = np.deg2rad(35.0)  # hard bank limit for the human

    # position / velocity controller
    kp_pos_xy: float = 0.7
    kp_pos_z: float = 1.3
    # keep velocity-loop P well under the tilt bandwidth and lean on D for
    # damping. that combo is what stops the heavy tilt-to-translate body from
    # falling into an attitude limit cycle. all tuned in SITL.
    kp_vel_xy: float = 2.0
    ki_vel_xy: float = 0.4              # soaks up wind without a limit cycle
    kd_vel_xy: float = 1.0
    kp_vel_z: float = 6.0
    ki_vel_z: float = 3.0
    kd_vel_z: float = 0.2
    vel_i_limit: float = 6.0           # m/s^2 anti-windup clamp on velocity I-term
    max_accel_xy: float = 5.0          # m/s^2 commanded accel clamp (~27 deg tilt)

    # attitude controller: P on quaternion error -> rate setpoint.
    # gains stay gentle on purpose; 120 kg at ~60 kg.m^2 pitch/yaw can't chase
    # aggressive rate demands without pinning the fans.
    kp_att_rp: float = 6.0             # roll/pitch tilt fast so velocity loop
    kp_att_yaw: float = 2.5            # has headroom; yaw can take its time
    att_rate_limit_rp: float = np.deg2rad(150.0)

    # rate controller: PID -> body torque. sized to live inside the cluster's
    # ~860 Nm pitch/yaw budget under normal demands.
    kp_rate: np.ndarray = field(
        default_factory=lambda: np.array([40.0, 200.0, 200.0]))
    ki_rate: np.ndarray = field(
        default_factory=lambda: np.array([12.0, 50.0, 50.0]))
    kd_rate: np.ndarray = field(
        default_factory=lambda: np.array([1.0, 5.0, 5.0]))
    rate_i_limit: np.ndarray = field(
        default_factory=lambda: np.array([30.0, 150.0, 150.0]))

    # geofence: keep-in volume + how we treat the boundary
    fence_ceiling: float = 150.0       # m soft ceiling. proper vertical Quidditch.
                                       # (see hardware/analysis/altitude_ceiling.py:
                                       # thrust margin holds to km, chute ok from here)
    fence_floor: float = 3.0           # m soft floor, never auto-descend below in flight
    fence_margin: float = 4.0          # m of braking room before the hard wall
    # lateral fence is a CCW convex polygon in world XY. default pitch is 100x50.
    fence_polygon: np.ndarray = field(default_factory=lambda: np.array([
        [-50.0, -25.0], [50.0, -25.0], [50.0, 25.0], [-50.0, 25.0],
    ]))

    # battery / failsafe
    batt_capacity_wh: float = 2600.0   # usable energy
    batt_hover_eta: float = 0.62       # electrical->aero efficiency in hover
    batt_rtp_soc: float = 0.30         # under this we Return To Pit
    batt_land_soc: float = 0.15        # under this we just land, now
    # pit lives inside the keep-in box, not parked against the hard wall
    pit_location: np.ndarray = field(default_factory=lambda: np.array([-38.0, 0.0]))
    pit_approach_alt: float = 8.0      # m cruise-home altitude

    # takeoff / landing
    takeoff_alt: float = 6.0
    takeoff_speed: float = 1.5
    land_speed: float = 0.8
    landed_alt: float = 0.15
    emergency_descent_speed: float = 1.2  # the gentle kill-switch descent

    def __post_init__(self) -> None:
        # callers sometimes hand us plain lists; coerce to float arrays
        self.inertia_diag = np.asarray(self.inertia_diag, dtype=float)
        self.fan_layout = np.asarray(self.fan_layout, dtype=float)
        self.fence_polygon = np.asarray(self.fence_polygon, dtype=float)

    @property
    def hover_thrust(self) -> float:
        return self.mass * GRAVITY

    @property
    def num_fans(self) -> int:
        return self.fan_layout.shape[0]
