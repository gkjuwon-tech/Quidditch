//! C ABI for the NIMBUS real-time control core.
//!
//! On layout: every FFI scalar is an f64. Keeping the field widths uniform
//! means the structs lay out predictably and a Python ctypes.Structure mirrors
//! them exactly -- no surprise padding sneaking across the boundary.
//!
//! Two build flavours:
//!   * default (feature "std"): a cdylib with heap create/destroy, what the
//!     Python ctypes host backend links against.
//!   * --no-default-features: #![no_std] for bare-metal flight MCUs. Use the
//!     placement-init API (nc_size + nc_init) and the target never touches a heap.
#![cfg_attr(not(feature = "std"), no_std)]

mod control;
mod math;

// the standalone embedded PoC build needs its own panic handler; real firmware
// brings one, so this stays behind an explicit feature gate.
#[cfg(all(not(feature = "std"), feature = "poc-panic"))]
#[panic_handler]
fn panic(_: &core::panic::PanicInfo) -> ! {
    loop {}
}

use control::{Controller, CoreParams, Out, NUM_FANS};

/// Every parameter, as f64. Arrays are row-major.
#[repr(C)]
pub struct FfiParams {
    pub dt: f64,
    pub pos_loop_div: f64,
    pub mass: f64,
    pub hover_thrust: f64,
    pub kp_pos_xy: f64,
    pub kp_pos_z: f64,
    pub max_accel_xy: f64,
    pub max_speed_xy: f64,
    pub max_climb_rate: f64,
    pub max_descent_rate: f64,
    pub max_tilt: f64,
    pub kp_att_rp: f64,
    pub kp_att_yaw: f64,
    pub att_rate_limit_rp: f64,
    pub max_yaw_rate: f64,
    pub fan_min: f64,
    pub fan_max: f64,
    pub num_fans: f64,
    pub vel_xy_kp: f64,
    pub vel_xy_ki: f64,
    pub vel_xy_kd: f64,
    pub vel_xy_ilim: f64,
    pub vel_z_kp: f64,
    pub vel_z_ki: f64,
    pub vel_z_kd: f64,
    pub vel_z_ilim: f64,
    pub rate_kp: [f64; 3],
    pub rate_ki: [f64; 3],
    pub rate_kd: [f64; 3],
    pub rate_ilim: [f64; 3],
    pub a: [f64; 32],     // 4x8 allocation matrix (row-major)
    pub apinv: [f64; 32], // 8x4 pseudo-inverse (row-major)
}

#[repr(C)]
pub struct FfiOut {
    pub fan: [f64; NUM_FANS],
    pub collective: f64,
    pub torque_cmd: [f64; 3],
    pub torque_actual: [f64; 3],
}

impl From<&FfiParams> for CoreParams {
    fn from(f: &FfiParams) -> Self {
        let mut a = [[0.0; NUM_FANS]; 4];
        let mut apinv = [[0.0; 4]; NUM_FANS];
        for k in 0..4 {
            for i in 0..NUM_FANS {
                a[k][i] = f.a[k * NUM_FANS + i];
            }
        }
        for i in 0..NUM_FANS {
            for j in 0..4 {
                apinv[i][j] = f.apinv[i * 4 + j];
            }
        }
        CoreParams {
            dt: f.dt,
            pos_loop_div: f.pos_loop_div as i32,
            mass: f.mass,
            hover_thrust: f.hover_thrust,
            kp_pos_xy: f.kp_pos_xy,
            kp_pos_z: f.kp_pos_z,
            max_accel_xy: f.max_accel_xy,
            max_speed_xy: f.max_speed_xy,
            max_climb_rate: f.max_climb_rate,
            max_descent_rate: f.max_descent_rate,
            max_tilt: f.max_tilt,
            kp_att_rp: f.kp_att_rp,
            kp_att_yaw: f.kp_att_yaw,
            att_rate_limit_rp: f.att_rate_limit_rp,
            max_yaw_rate: f.max_yaw_rate,
            fan_min: f.fan_min,
            fan_max: f.fan_max,
            num_fans: f.num_fans as usize,
            a,
            apinv,
            vel_xy: (f.vel_xy_kp, f.vel_xy_ki, f.vel_xy_kd, f.vel_xy_ilim),
            vel_z: (f.vel_z_kp, f.vel_z_ki, f.vel_z_kd, f.vel_z_ilim),
            rate_kp: f.rate_kp,
            rate_ki: f.rate_ki,
            rate_kd: f.rate_kd,
            rate_ilim: f.rate_ilim,
        }
    }
}

/// Build a controller on the heap and hand back an opaque handle; free it with
/// `nc_destroy`. Host-only (wants std/alloc) -- embedded goes through `nc_init`.
///
/// # Safety
/// `params` must point to a valid `FfiParams`.
#[cfg(feature = "std")]
#[no_mangle]
pub unsafe extern "C" fn nc_create(params: *const FfiParams) -> *mut Controller {
    if params.is_null() {
        return core::ptr::null_mut();
    }
    let cp = CoreParams::from(&*params);
    Box::into_raw(Box::new(Controller::new(cp)))
}

/// Free a heap controller. Host-only.
///
/// # Safety
/// `ctrl` must have come from `nc_create`, and must not be touched afterwards.
#[cfg(feature = "std")]
#[no_mangle]
pub unsafe extern "C" fn nc_destroy(ctrl: *mut Controller) {
    if !ctrl.is_null() {
        drop(Box::from_raw(ctrl));
    }
}

// no-alloc placement API -- works on bare metal, never asks for a heap
/// Size of a `Controller` in bytes, so firmware can carve out static storage.
#[no_mangle]
pub extern "C" fn nc_size() -> usize {
    core::mem::size_of::<Controller>()
}

/// Required alignment of `Controller`.
#[no_mangle]
pub extern "C" fn nc_align() -> usize {
    core::mem::align_of::<Controller>()
}

/// Construct a controller into caller-provided storage (no heap).
///
/// # Safety
/// `slot` must point to writable memory of at least `nc_size()` bytes with
/// `nc_align()` alignment; `params` must be valid.
#[no_mangle]
pub unsafe extern "C" fn nc_init(slot: *mut Controller, params: *const FfiParams) {
    if slot.is_null() || params.is_null() {
        return;
    }
    let cp = CoreParams::from(&*params);
    core::ptr::write(slot, Controller::new(cp));
}

/// # Safety
/// `ctrl` must come from `nc_create`.
#[no_mangle]
pub unsafe extern "C" fn nc_reset(ctrl: *mut Controller) {
    if let Some(c) = ctrl.as_mut() {
        c.reset();
    }
}

/// Run a single control tick: `state` is 13 f64, `sp` is 8 f64, `out` is filled in.
///
/// # Safety
/// All pointers must be valid and correctly sized; `ctrl` from `nc_create`.
#[no_mangle]
pub unsafe extern "C" fn nc_control(
    ctrl: *mut Controller,
    state: *const f64,
    sp: *const f64,
    out: *mut FfiOut,
) {
    let c = match ctrl.as_mut() {
        Some(c) => c,
        None => return,
    };
    let mut st = [0.0f64; 13];
    let mut spp = [0.0f64; 8];
    core::ptr::copy_nonoverlapping(state, st.as_mut_ptr(), 13);
    core::ptr::copy_nonoverlapping(sp, spp.as_mut_ptr(), 8);

    let Out { fan, collective, torque_cmd, torque_actual } = c.control(&st, &spp);

    if let Some(o) = out.as_mut() {
        o.fan = fan;
        o.collective = collective;
        o.torque_cmd = torque_cmd;
        o.torque_actual = torque_actual;
    }
}
