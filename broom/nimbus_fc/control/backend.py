"""Swappable control backends for the inner cascade.

Both backends expose the same interface:

    control(state, setpoint, dt) -> (fan_thrusts, collective, torque_cmd, torque_actual)
    reset()

`PyControlBackend` runs the pure-Python cascade (development; what the rest of
the package was built on). `RustControlBackend` drives the compiled
`nimbus_core` cdylib through ctypes -- same algorithm, but in a deterministic,
GC-free, allocation-free control path for hard real time.

The split is deliberate: policy/safety logic (commander, geofence, intent) stays
in expressive Python; the high-rate numeric loop where "if it stutters, someone
falls" runs in Rust.
"""

from __future__ import annotations

import ctypes
import os

import numpy as np

from ..core.params import Params
from ..core.types import Setpoint, State
from .attitude import AttitudeController
from .mixer import Mixer
from .position import PositionController
from .rate import RateController

NUM_FANS = 8


class PyControlBackend:
    name = "python"

    def __init__(self, params: Params):
        self.p = params
        self.position = PositionController(params)
        self.attitude = AttitudeController(params)
        self.rate = RateController(params)
        self.mixer = Mixer(params)
        self._tick = 0
        self._collective = params.hover_thrust
        self._q_des = np.array([1.0, 0.0, 0.0, 0.0])
        self._yaw_rate_ff = 0.0

    def reset(self) -> None:
        self.position.reset()
        self.rate.reset()
        self._tick = 0
        self._collective = self.p.hover_thrust
        self._q_des = np.array([1.0, 0.0, 0.0, 0.0])
        self._yaw_rate_ff = 0.0

    def control(self, state: State, sp: Setpoint, dt: float):
        if self._tick % self.p.pos_loop_div == 0:
            self._collective, self._q_des, self._yaw_rate_ff = \
                self.position.update(sp, state, dt * self.p.pos_loop_div)
        self._tick += 1
        rate_sp = self.attitude.update(state.quat, self._q_des, self._yaw_rate_ff)
        torque = self.rate.update(rate_sp, state.omega, dt)
        fan, actual = self.mixer.allocate(self._collective, torque)
        return fan, self._collective, torque, actual


# --- rust backend (ctypes) ------------------------------------------------------

class _FfiParams(ctypes.Structure):
    _fields_ = [
        ("dt", ctypes.c_double),
        ("pos_loop_div", ctypes.c_double),
        ("mass", ctypes.c_double),
        ("hover_thrust", ctypes.c_double),
        ("kp_pos_xy", ctypes.c_double),
        ("kp_pos_z", ctypes.c_double),
        ("max_accel_xy", ctypes.c_double),
        ("max_speed_xy", ctypes.c_double),
        ("max_climb_rate", ctypes.c_double),
        ("max_descent_rate", ctypes.c_double),
        ("max_tilt", ctypes.c_double),
        ("kp_att_rp", ctypes.c_double),
        ("kp_att_yaw", ctypes.c_double),
        ("att_rate_limit_rp", ctypes.c_double),
        ("max_yaw_rate", ctypes.c_double),
        ("fan_min", ctypes.c_double),
        ("fan_max", ctypes.c_double),
        ("num_fans", ctypes.c_double),
        ("vel_xy_kp", ctypes.c_double),
        ("vel_xy_ki", ctypes.c_double),
        ("vel_xy_kd", ctypes.c_double),
        ("vel_xy_ilim", ctypes.c_double),
        ("vel_z_kp", ctypes.c_double),
        ("vel_z_ki", ctypes.c_double),
        ("vel_z_kd", ctypes.c_double),
        ("vel_z_ilim", ctypes.c_double),
        ("rate_kp", ctypes.c_double * 3),
        ("rate_ki", ctypes.c_double * 3),
        ("rate_kd", ctypes.c_double * 3),
        ("rate_ilim", ctypes.c_double * 3),
        ("a", ctypes.c_double * 32),
        ("apinv", ctypes.c_double * 32),
    ]


class _FfiOut(ctypes.Structure):
    _fields_ = [
        ("fan", ctypes.c_double * NUM_FANS),
        ("collective", ctypes.c_double),
        ("torque_cmd", ctypes.c_double * 3),
        ("torque_actual", ctypes.c_double * 3),
    ]


def _default_lib_path() -> str:
    here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(here, "rust", "nimbus_core", "target", "release",
                        "libnimbus_core.so")


def rust_available(lib_path: str | None = None) -> bool:
    return os.path.exists(lib_path or _default_lib_path())


class RustControlBackend:
    name = "rust"

    def __init__(self, params: Params, lib_path: str | None = None):
        self.p = params
        path = lib_path or _default_lib_path()
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"nimbus_core not built: {path}\n"
                f"build it with:  cd rust/nimbus_core && cargo build --release")
        self.lib = ctypes.CDLL(path)
        self.lib.nc_create.argtypes = [ctypes.POINTER(_FfiParams)]
        self.lib.nc_create.restype = ctypes.c_void_p
        self.lib.nc_reset.argtypes = [ctypes.c_void_p]
        self.lib.nc_destroy.argtypes = [ctypes.c_void_p]
        self.lib.nc_control.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(ctypes.c_double),
            ctypes.POINTER(ctypes.c_double), ctypes.POINTER(_FfiOut)]

        fp = self._build_ffi_params(params)
        self.ctrl = self.lib.nc_create(ctypes.byref(fp))
        if not self.ctrl:
            raise RuntimeError("nc_create returned null")

        self._out = _FfiOut()
        self._state = (ctypes.c_double * 13)()
        self._sp = (ctypes.c_double * 8)()

    @staticmethod
    def _build_ffi_params(p: Params) -> _FfiParams:
        mix = Mixer(p)  # reuse the validated allocation + pseudo-inverse
        fp = _FfiParams()
        fp.dt = p.dt
        fp.pos_loop_div = float(p.pos_loop_div)
        fp.mass = p.mass
        fp.hover_thrust = p.hover_thrust
        fp.kp_pos_xy = p.kp_pos_xy
        fp.kp_pos_z = p.kp_pos_z
        fp.max_accel_xy = p.max_accel_xy
        fp.max_speed_xy = p.max_speed_xy
        fp.max_climb_rate = p.max_climb_rate
        fp.max_descent_rate = p.max_descent_rate
        fp.max_tilt = p.max_tilt
        fp.kp_att_rp = p.kp_att_rp
        fp.kp_att_yaw = p.kp_att_yaw
        fp.att_rate_limit_rp = p.att_rate_limit_rp
        fp.max_yaw_rate = p.max_yaw_rate
        fp.fan_min = p.fan_thrust_min
        fp.fan_max = p.fan_thrust_max
        fp.num_fans = float(p.num_fans)
        fp.vel_xy_kp, fp.vel_xy_ki, fp.vel_xy_kd, fp.vel_xy_ilim = \
            p.kp_vel_xy, p.ki_vel_xy, p.kd_vel_xy, p.vel_i_limit
        fp.vel_z_kp, fp.vel_z_ki, fp.vel_z_kd, fp.vel_z_ilim = \
            p.kp_vel_z, p.ki_vel_z, p.kd_vel_z, p.vel_i_limit
        fp.rate_kp[:] = list(map(float, p.kp_rate))
        fp.rate_ki[:] = list(map(float, p.ki_rate))
        fp.rate_kd[:] = list(map(float, p.kd_rate))
        fp.rate_ilim[:] = list(map(float, p.rate_i_limit))
        fp.a[:] = list(map(float, mix.A.flatten()))           # 4x8 row-major
        fp.apinv[:] = list(map(float, mix.A_pinv.flatten()))   # 8x4 row-major
        return fp

    def reset(self) -> None:
        self.lib.nc_reset(self.ctrl)

    def control(self, state: State, sp: Setpoint, dt: float):
        st = self._state
        st[0:3] = list(map(float, state.pos))
        st[3:6] = list(map(float, state.vel))
        st[6:10] = list(map(float, state.quat))
        st[10:13] = list(map(float, state.omega))

        spp = self._sp
        if sp.pos is None:
            spp[0:3] = [np.nan, np.nan, np.nan]
        else:
            spp[0:3] = list(map(float, sp.pos))
        spp[3:6] = list(map(float, sp.vel_ff))
        spp[6] = float(sp.yaw) if sp.yaw is not None else np.nan
        spp[7] = float(sp.yaw_rate_ff)

        self.lib.nc_control(self.ctrl, st, spp, ctypes.byref(self._out))
        o = self._out
        return (np.array(o.fan, dtype=float), float(o.collective),
                np.array(o.torque_cmd, dtype=float),
                np.array(o.torque_actual, dtype=float))

    def __del__(self):
        try:
            if getattr(self, "ctrl", None):
                self.lib.nc_destroy(self.ctrl)
                self.ctrl = None
        except Exception:
            pass


def make_backend(params: Params, backend: str = "python"):
    if backend == "python":
        return PyControlBackend(params)
    if backend == "rust":
        return RustControlBackend(params)
    raise ValueError(f"unknown backend '{backend}' (use 'python' or 'rust')")
