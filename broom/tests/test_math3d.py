"""sanity tests for the quaternion/rotation core. run: python -m pytest -q."""

import numpy as np

from nimbus_fc.core import math3d as m


def test_identity_rotation():
    v = m.vec3(1, 2, 3)
    assert np.allclose(m.quat_rotate(m.quat_identity(), v), v)


def test_euler_roundtrip():
    for rpy in [(0.1, -0.2, 0.3), (0.5, 0.0, -1.2), (-0.3, 0.4, 2.0)]:
        q = m.quat_from_euler(*rpy)
        back = m.quat_to_euler(q)
        assert np.allclose(back, rpy, atol=1e-6)


def test_rotmat_quat_roundtrip():
    q = m.quat_from_euler(0.3, -0.4, 1.1)
    R = m.quat_to_rotmat(q)
    q2 = m.rotmat_to_quat(R)
    # quat double-cover: compare via rotation action, not the raw components
    v = m.vec3(1, -2, 0.5)
    assert np.allclose(m.quat_rotate(q, v), m.quat_rotate(q2, v), atol=1e-9)


def test_rotation_matrix_orthonormal():
    q = m.quat_from_euler(0.7, 0.2, -0.9)
    R = m.quat_to_rotmat(q)
    assert np.allclose(R @ R.T, np.eye(3), atol=1e-9)
    assert np.isclose(np.linalg.det(R), 1.0, atol=1e-9)


def test_inverse_rotation():
    q = m.quat_from_euler(0.2, 0.3, 0.4)
    v = m.vec3(3, 1, -2)
    w = m.quat_rotate(q, v)
    assert np.allclose(m.quat_rotate_inv(q, w), v, atol=1e-9)


def test_integrate_constant_yaw_rate():
    q = m.quat_identity()
    omega = m.vec3(0, 0, 1.0)  # 1 rad/s yaw
    dt = 0.001
    for _ in range(1000):       # one second
        q = m.quat_integrate(q, omega, dt)
    yaw = m.quat_to_euler(q)[2]
    assert abs(yaw - 1.0) < 1e-2


def test_error_axis_drives_toward_target():
    q_cur = m.quat_identity()
    q_des = m.quat_from_euler(0.0, 0.0, 0.3)
    err = m.quat_error_angle_axis(q_cur, q_des)
    # error about +z (yaw), small-angle ~ 0.3
    assert err[2] > 0.25 and abs(err[0]) < 1e-6 and abs(err[1]) < 1e-6
