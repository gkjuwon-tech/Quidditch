//! Just enough f64 vector/quaternion math to match nimbus_fc.core.math3d
//! exactly. Conventions: world ENU (z up), quaternion q=[w,x,y,z] rotates
//! body -> world.

#[allow(dead_code)] // part of the public math API; the control core just doesn't happen to use it
pub const GRAVITY: f64 = 9.80665;
pub const EPS: f64 = 1e-9;

pub type V3 = [f64; 3];
pub type Quat = [f64; 4];

// transcendentals go through libm so the core still builds on no_std targets,
// where the std f64 methods aren't available. using them everywhere also keeps
// host and embedded bit-identical.
#[inline] pub(crate) fn sqrt(x: f64) -> f64 { libm::sqrt(x) }
#[inline] pub(crate) fn sin(x: f64) -> f64 { libm::sin(x) }
#[inline] pub(crate) fn cos(x: f64) -> f64 { libm::cos(x) }
#[inline] pub(crate) fn tan(x: f64) -> f64 { libm::tan(x) }
#[inline] pub(crate) fn atan2(y: f64, x: f64) -> f64 { libm::atan2(y, x) }

#[inline]
pub fn dot3(a: V3, b: V3) -> f64 {
    a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
}

#[inline]
pub fn norm3(a: V3) -> f64 {
    sqrt(dot3(a, a))
}

#[inline]
pub fn cross3(a: V3, b: V3) -> V3 {
    [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]
}

#[inline]
pub fn normalize3(v: V3, fallback: V3) -> V3 {
    let n = norm3(v);
    if n < EPS {
        fallback
    } else {
        [v[0] / n, v[1] / n, v[2] / n]
    }
}

/// Scale v down so |v| <= max_norm, keeping its direction.
#[inline]
pub fn clamp_norm(v: &mut [f64], max_norm: f64) {
    let mut s = 0.0;
    for &x in v.iter() {
        s += x * x;
    }
    let n = sqrt(s);
    if n > max_norm && n > EPS {
        let k = max_norm / n;
        for x in v.iter_mut() {
            *x *= k;
        }
    }
}

#[inline]
pub fn quat_mul(a: Quat, b: Quat) -> Quat {
    let (aw, ax, ay, az) = (a[0], a[1], a[2], a[3]);
    let (bw, bx, by, bz) = (b[0], b[1], b[2], b[3]);
    [
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    ]
}

#[inline]
pub fn quat_conj(q: Quat) -> Quat {
    [q[0], -q[1], -q[2], -q[3]]
}

/// Rotate a body-frame vector into world: q (x) [0,v] (x) q^-1.
pub fn quat_rotate(q: Quat, v: V3) -> V3 {
    let qv = [0.0, v[0], v[1], v[2]];
    let r = quat_mul(quat_mul(q, qv), quat_conj(q));
    [r[1], r[2], r[3]]
}

pub fn quat_normalize(q: Quat) -> Quat {
    let n = sqrt(q[0] * q[0] + q[1] * q[1] + q[2] * q[2] + q[3] * q[3]);
    if n < EPS {
        return [1.0, 0.0, 0.0, 0.0];
    }
    let s = if q[0] < 0.0 { -1.0 / n } else { 1.0 / n };
    [q[0] * s, q[1] * s, q[2] * s, q[3] * s]
}

/// Small-signal attitude error as a body-frame rotation vector, ~2*vec(q_err).
pub fn quat_error_angle_axis(q_cur: Quat, q_des: Quat) -> V3 {
    let mut qe = quat_mul(quat_conj(q_cur), q_des);
    if qe[0] < 0.0 {
        qe = [-qe[0], -qe[1], -qe[2], -qe[3]];
    }
    [2.0 * qe[1], 2.0 * qe[2], 2.0 * qe[3]]
}

/// Pull the ZYX yaw out of a quaternion.
pub fn yaw_of(q: Quat) -> f64 {
    let (w, x, y, z) = (q[0], q[1], q[2], q[3]);
    let siny_cosp = 2.0 * (w * z + x * y);
    let cosy_cosp = 1.0 - 2.0 * (y * y + z * z);
    atan2(siny_cosp, cosy_cosp)
}

/// Build the body->world quaternion that puts body-z along the thrust vector
/// at the given yaw. Mirrors PositionController._attitude_from_thrust + rotmat_to_quat.
pub fn attitude_from_thrust(thrust_vec: V3, yaw: f64) -> Quat {
    let zb = normalize3(thrust_vec, [0.0, 0.0, 1.0]);
    let xc = [cos(yaw), sin(yaw), 0.0];
    let yb = normalize3(cross3(zb, xc), [0.0, 1.0, 0.0]);
    let xb = cross3(yb, zb);
    // the columns of R are xb, yb, zb -- the body axes expressed in world
    rotmat_to_quat([
        [xb[0], yb[0], zb[0]],
        [xb[1], yb[1], zb[1]],
        [xb[2], yb[2], zb[2]],
    ])
}

/// Rotation matrix -> quaternion via Shepperd's method; matches math3d.rotmat_to_quat.
pub fn rotmat_to_quat(r: [[f64; 3]; 3]) -> Quat {
    let tr = r[0][0] + r[1][1] + r[2][2];
    let q = if tr > 0.0 {
        let s = sqrt(tr + 1.0) * 2.0;
        [
            0.25 * s,
            (r[2][1] - r[1][2]) / s,
            (r[0][2] - r[2][0]) / s,
            (r[1][0] - r[0][1]) / s,
        ]
    } else if r[0][0] > r[1][1] && r[0][0] > r[2][2] {
        let s = sqrt(1.0 + r[0][0] - r[1][1] - r[2][2]) * 2.0;
        [
            (r[2][1] - r[1][2]) / s,
            0.25 * s,
            (r[0][1] + r[1][0]) / s,
            (r[0][2] + r[2][0]) / s,
        ]
    } else if r[1][1] > r[2][2] {
        let s = sqrt(1.0 + r[1][1] - r[0][0] - r[2][2]) * 2.0;
        [
            (r[0][2] - r[2][0]) / s,
            (r[0][1] + r[1][0]) / s,
            0.25 * s,
            (r[1][2] + r[2][1]) / s,
        ]
    } else {
        let s = sqrt(1.0 + r[2][2] - r[0][0] - r[1][1]) * 2.0;
        [
            (r[1][0] - r[0][1]) / s,
            (r[0][2] + r[2][0]) / s,
            (r[1][2] + r[2][1]) / s,
            0.25 * s,
        ]
    };
    quat_normalize(q)
}

#[inline]
pub fn clip(x: f64, lo: f64, hi: f64) -> f64 {
    if x < lo {
        lo
    } else if x > hi {
        hi
    } else {
        x
    }
}
