"""3D math primitives: vectors, quaternions, rotations.

Conventions (locked across the whole stack):
  - World frame: ENU. x=East, y=North, z=Up. Gravity points to -z.
  - Quaternion q = [w, x, y, z], unit norm, rotates body -> world:
        v_world = q (x) v_body (x) q^-1
  - Body frame: x=forward, y=left, z=up. Lift/thrust acts along +body z.

Benchmarked against the quaternion conventions used in PX4 (px4_msgs) and
the Crazyflie firmware estimator. We deliberately avoid scipy so the whole
project runs on numpy alone.
"""

from __future__ import annotations

import numpy as np

GRAVITY = 9.80665  # m/s^2
EPS = 1e-9


# --------------------------------------------------------------------------- #
# Vectors
# --------------------------------------------------------------------------- #
def vec3(x: float = 0.0, y: float = 0.0, z: float = 0.0) -> np.ndarray:
    return np.array([x, y, z], dtype=float)


def normalize(v: np.ndarray, fallback: np.ndarray | None = None) -> np.ndarray:
    """Return v/|v|; if v is ~zero return `fallback` (or v unchanged)."""
    n = float(np.linalg.norm(v))
    if n < EPS:
        return v if fallback is None else fallback
    return v / n


def clamp_norm(v: np.ndarray, max_norm: float) -> np.ndarray:
    """Scale v down so |v| <= max_norm. Direction preserved."""
    n = float(np.linalg.norm(v))
    if n > max_norm and n > EPS:
        return v * (max_norm / n)
    return v


# --------------------------------------------------------------------------- #
# Quaternions  (q = [w, x, y, z])
# --------------------------------------------------------------------------- #
def quat_identity() -> np.ndarray:
    return np.array([1.0, 0.0, 0.0, 0.0])


def quat_normalize(q: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(q))
    if n < EPS:
        return quat_identity()
    q = q / n
    # Keep a canonical hemisphere (w >= 0) to avoid double-cover sign flips.
    return -q if q[0] < 0.0 else q


def quat_mul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Hamilton product a (x) b."""
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return np.array([
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    ])


def quat_conj(q: np.ndarray) -> np.ndarray:
    return np.array([q[0], -q[1], -q[2], -q[3]])


def quat_rotate(q: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Rotate vector v (body) into world: q (x) [0,v] (x) q^-1."""
    qv = np.array([0.0, v[0], v[1], v[2]])
    return quat_mul(quat_mul(q, qv), quat_conj(q))[1:]


def quat_rotate_inv(q: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Rotate vector v (world) into body."""
    return quat_rotate(quat_conj(q), v)


def quat_to_rotmat(q: np.ndarray) -> np.ndarray:
    """Body->world rotation matrix R, columns are body axes in world."""
    w, x, y, z = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - w * z),     2 * (x * z + w * y)],
        [2 * (x * y + w * z),     1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
        [2 * (x * z - w * y),     2 * (y * z + w * x),     1 - 2 * (x * x + y * y)],
    ])


def rotmat_to_quat(R: np.ndarray) -> np.ndarray:
    """Convert a proper rotation matrix to a unit quaternion (Shepperd's method)."""
    tr = R[0, 0] + R[1, 1] + R[2, 2]
    if tr > 0.0:
        s = np.sqrt(tr + 1.0) * 2.0
        w = 0.25 * s
        x = (R[2, 1] - R[1, 2]) / s
        y = (R[0, 2] - R[2, 0]) / s
        z = (R[1, 0] - R[0, 1]) / s
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2.0
        w = (R[2, 1] - R[1, 2]) / s
        x = 0.25 * s
        y = (R[0, 1] + R[1, 0]) / s
        z = (R[0, 2] + R[2, 0]) / s
    elif R[1, 1] > R[2, 2]:
        s = np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2.0
        w = (R[0, 2] - R[2, 0]) / s
        x = (R[0, 1] + R[1, 0]) / s
        y = 0.25 * s
        z = (R[1, 2] + R[2, 1]) / s
    else:
        s = np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2.0
        w = (R[1, 0] - R[0, 1]) / s
        x = (R[0, 2] + R[2, 0]) / s
        y = (R[1, 2] + R[2, 1]) / s
        z = 0.25 * s
    return quat_normalize(np.array([w, x, y, z]))


def quat_from_euler(roll: float, pitch: float, yaw: float) -> np.ndarray:
    """ZYX intrinsic (yaw, then pitch, then roll). Angles in radians."""
    cr, sr = np.cos(roll / 2), np.sin(roll / 2)
    cp, sp = np.cos(pitch / 2), np.sin(pitch / 2)
    cy, sy = np.cos(yaw / 2), np.sin(yaw / 2)
    return quat_normalize(np.array([
        cr * cp * cy + sr * sp * sy,
        sr * cp * cy - cr * sp * sy,
        cr * sp * cy + sr * cp * sy,
        cr * cp * sy - sr * sp * cy,
    ]))


def quat_to_euler(q: np.ndarray) -> np.ndarray:
    """Return [roll, pitch, yaw] (rad), ZYX. Gimbal-safe-ish via clamping."""
    w, x, y, z = q
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x * x + y * y)
    roll = np.arctan2(sinr_cosp, cosr_cosp)
    sinp = 2 * (w * y - z * x)
    pitch = np.arcsin(np.clip(sinp, -1.0, 1.0))
    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    yaw = np.arctan2(siny_cosp, cosy_cosp)
    return np.array([roll, pitch, yaw])


def quat_integrate(q: np.ndarray, omega_body: np.ndarray, dt: float) -> np.ndarray:
    """Integrate attitude given body angular rate. q_dot = 0.5 q (x) [0, w]."""
    qw = np.array([0.0, omega_body[0], omega_body[1], omega_body[2]])
    qdot = 0.5 * quat_mul(q, qw)
    return quat_normalize(q + qdot * dt)


def quat_error_angle_axis(q_cur: np.ndarray, q_des: np.ndarray) -> np.ndarray:
    """Small-signal attitude error as a rotation vector in the BODY frame.

    Returns ~ 2 * vec(q_err) where q_err = q_cur^-1 (x) q_des. This is the
    classic PX4 attitude error used to drive the rate setpoint.
    """
    q_err = quat_mul(quat_conj(q_cur), q_des)
    if q_err[0] < 0.0:  # shortest path
        q_err = -q_err
    return 2.0 * q_err[1:]


def yaw_of(q: np.ndarray) -> float:
    return float(quat_to_euler(q)[2])


def skew(v: np.ndarray) -> np.ndarray:
    """Skew-symmetric matrix [v]_x such that [v]_x @ w == cross(v, w)."""
    return np.array([
        [0.0, -v[2], v[1]],
        [v[2], 0.0, -v[0]],
        [-v[1], v[0], 0.0],
    ])


def quat_from_rotvec(rv: np.ndarray) -> np.ndarray:
    """Exponential map: rotation vector (axis*angle) -> unit quaternion."""
    angle = float(np.linalg.norm(rv))
    if angle < EPS:
        return quat_identity()
    axis = rv / angle
    s = np.sin(angle / 2.0)
    return np.array([np.cos(angle / 2.0), axis[0] * s, axis[1] * s, axis[2] * s])
