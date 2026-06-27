//! Cascaded control core, kept in parity with nimbus_fc.control.{pid,position,attitude,rate,mixer}.
//! Fixed-size, allocation-free control path. NUM_FANS pinned at 8.

use crate::math::*;

pub const NUM_FANS: usize = 8;

/// Vector PID with anti-windup + derivative-on-measurement (matches pid.PID).
pub struct Pid<const N: usize> {
    kp: [f64; N],
    ki: [f64; N],
    kd: [f64; N],
    ilim: [f64; N],
    integ: [f64; N],
    prev: [f64; N],
    has_prev: bool,
}

impl<const N: usize> Pid<N> {
    pub fn new(kp: [f64; N], ki: [f64; N], kd: [f64; N], ilim: [f64; N]) -> Self {
        Pid { kp, ki, kd, ilim, integ: [0.0; N], prev: [0.0; N], has_prev: false }
    }

    pub fn reset(&mut self) {
        self.integ = [0.0; N];
        self.has_prev = false;
    }

    pub fn update(&mut self, sp: [f64; N], meas: [f64; N], dt: f64) -> [f64; N] {
        let mut out = [0.0; N];
        for i in 0..N {
            let err = sp[i] - meas[i];
            self.integ[i] = clip(self.integ[i] + self.ki[i] * err * dt,
                                 -self.ilim[i], self.ilim[i]);
            let d_meas = if self.has_prev { (meas[i] - self.prev[i]) / dt } else { 0.0 };
            out[i] = self.kp[i] * err + self.integ[i] - self.kd[i] * d_meas;
            self.prev[i] = meas[i];
        }
        self.has_prev = true;
        out
    }
}

/// Plain-old-data parameters (filled from the FFI struct in lib.rs).
#[derive(Clone)]
pub struct CoreParams {
    pub dt: f64,
    pub pos_loop_div: i32,
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
    pub num_fans: usize,
    pub a: [[f64; NUM_FANS]; 4],     // allocation matrix [T, tx, ty, tz] = A f
    pub apinv: [[f64; 4]; NUM_FANS], // pseudo-inverse f = A+ wrench
    pub vel_xy: (f64, f64, f64, f64), // kp, ki, kd, ilim (scalar -> broadcast)
    pub vel_z: (f64, f64, f64, f64),
    pub rate_kp: [f64; 3],
    pub rate_ki: [f64; 3],
    pub rate_kd: [f64; 3],
    pub rate_ilim: [f64; 3],
}

pub struct Controller {
    p: CoreParams,
    rate_pid: Pid<3>,
    vel_xy_pid: Pid<2>,
    vel_z_pid: Pid<1>,
    tick: u64,
    collective: f64,
    q_des: Quat,
    yaw_rate_ff: f64,
}

/// One control tick's output.
pub struct Out {
    pub fan: [f64; NUM_FANS],
    pub collective: f64,
    pub torque_cmd: V3,
    pub torque_actual: V3,
}

impl Controller {
    pub fn new(p: CoreParams) -> Self {
        let (vxk, vxi, vxd, vxl) = p.vel_xy;
        let (vzk, vzi, vzd, vzl) = p.vel_z;
        let rate_pid = Pid::new(p.rate_kp, p.rate_ki, p.rate_kd, p.rate_ilim);
        let vel_xy_pid = Pid::new([vxk, vxk], [vxi, vxi], [vxd, vxd], [vxl, vxl]);
        let vel_z_pid = Pid::new([vzk], [vzi], [vzd], [vzl]);
        Controller {
            p, rate_pid, vel_xy_pid, vel_z_pid,
            tick: 0, collective: 0.0, q_des: [1.0, 0.0, 0.0, 0.0], yaw_rate_ff: 0.0,
        }
    }

    pub fn reset(&mut self) {
        self.rate_pid.reset();
        self.vel_xy_pid.reset();
        self.vel_z_pid.reset();
        self.tick = 0;
        self.collective = self.p.hover_thrust;
        self.q_des = [1.0, 0.0, 0.0, 0.0];
        self.yaw_rate_ff = 0.0;
    }

    /// state = [px,py,pz, vx,vy,vz, qw,qx,qy,qz, wx,wy,wz]
    /// sp    = [spx,spy,spz, vffx,vffy,vffz, yaw, yawrate]  (NaN = "not set")
    pub fn control(&mut self, state: &[f64; 13], sp: &[f64; 8]) -> Out {
        let p = &self.p;
        let pos = [state[0], state[1], state[2]];
        let vel = [state[3], state[4], state[5]];
        let quat = [state[6], state[7], state[8], state[9]];
        let omega = [state[10], state[11], state[12]];

        // Outer loop (position) at reduced rate
        if self.tick % (p.pos_loop_div as u64) == 0 {
            let dt_pos = p.dt * p.pos_loop_div as f64;
            self.position(&pos, &vel, &quat, sp, dt_pos);
        }
        self.tick += 1;

        // Attitude: quat error -> rate setpoint
        let err = quat_error_angle_axis(quat, self.q_des);
        let mut rate_sp = [
            self.p.kp_att_rp * err[0],
            self.p.kp_att_rp * err[1],
            self.p.kp_att_yaw * err[2] + self.yaw_rate_ff,
        ];
        let rl = [self.p.att_rate_limit_rp, self.p.att_rate_limit_rp, self.p.max_yaw_rate];
        for i in 0..3 {
            rate_sp[i] = clip(rate_sp[i], -rl[i], rl[i]);
        }

        // Rate: pid -> torque
        let torque = self.rate_pid.update(rate_sp, omega, self.p.dt);

        // Mixer
        self.allocate(self.collective, torque)
    }

    fn position(&mut self, pos: &V3, vel: &V3, quat: &Quat, sp: &[f64; 8], dt: f64) {
        let p = &self.p;
        // horizontal
        let mut vsp_xy = [sp[3], sp[4]];
        if sp[0].is_finite() && sp[1].is_finite() {
            let err = [sp[0] - pos[0], sp[1] - pos[1]];
            let dist = sqrt(err[0] * err[0] + err[1] * err[1]);
            if dist > 1e-6 {
                let a_brake = 0.7 * p.max_accel_xy;
                let v_des = (p.kp_pos_xy * dist)
                    .min(sqrt(2.0 * a_brake * dist))
                    .min(p.max_speed_xy);
                vsp_xy[0] += err[0] / dist * v_des;
                vsp_xy[1] += err[1] / dist * v_des;
            }
        }
        clamp_norm(&mut vsp_xy, p.max_speed_xy);
        let mut acc_xy = self.vel_xy_pid.update(vsp_xy, [vel[0], vel[1]], dt);
        clamp_norm(&mut acc_xy, p.max_accel_xy);

        // vertical
        let mut vsp_z = sp[5];
        if sp[2].is_finite() {
            vsp_z += p.kp_pos_z * (sp[2] - pos[2]);
        }
        vsp_z = clip(vsp_z, -p.max_descent_rate, p.max_climb_rate);
        let acc_z = self.vel_z_pid.update([vsp_z], [vel[2]], dt)[0];

        // desired thrust vector (gravity compensated) + tilt limit
        let mut tv = [p.mass * acc_xy[0], p.mass * acc_xy[1], p.mass * acc_z + p.hover_thrust];
        let z = tv[2].max(1e-3);
        let xy_norm = sqrt(tv[0] * tv[0] + tv[1] * tv[1]);
        let max_xy = z * tan(p.max_tilt);
        if xy_norm > max_xy && xy_norm > 1e-9 {
            let k = max_xy / xy_norm;
            tv[0] *= k;
            tv[1] *= k;
        }
        tv[2] = z;

        let body_z = quat_rotate(*quat, [0.0, 0.0, 1.0]);
        self.collective = dot3(tv, body_z).max(0.2 * p.hover_thrust);
        let yaw_des = if sp[6].is_finite() { sp[6] } else { yaw_of(*quat) };
        self.q_des = attitude_from_thrust(tv, yaw_des);
        self.yaw_rate_ff = sp[7];
    }

    fn allocate(&self, collective: f64, torque: V3) -> Out {
        let p = &self.p;
        let wrench = [collective, torque[0], torque[1], torque[2]];
        let mut f = self.apinv_mul(&wrench);

        let needs = f.iter().any(|&x| x < p.fan_min || x > p.fan_max);
        if needs {
            f = self.desaturate(&wrench);
        }
        for x in f.iter_mut() {
            *x = clip(*x, p.fan_min, p.fan_max);
        }

        // actual wrench = A f
        let mut actual = [0.0; 4];
        for k in 0..4 {
            let mut s = 0.0;
            for i in 0..p.num_fans {
                s += p.a[k][i] * f[i];
            }
            actual[k] = s;
        }
        Out {
            fan: f,
            collective,
            torque_cmd: torque,
            torque_actual: [actual[1], actual[2], actual[3]],
        }
    }

    fn apinv_mul(&self, wrench: &[f64; 4]) -> [f64; NUM_FANS] {
        let p = &self.p;
        let mut f = [0.0; NUM_FANS];
        for i in 0..p.num_fans {
            let mut s = 0.0;
            for j in 0..4 {
                s += p.apinv[i][j] * wrench[j];
            }
            f[i] = s;
        }
        f
    }

    /// Prioritize torque over collective under saturation (matches Mixer._desaturate).
    fn desaturate(&self, wrench: &[f64; 4]) -> [f64; NUM_FANS] {
        let p = &self.p;
        let tw = [0.0, wrench[1], wrench[2], wrench[3]];
        let f_tau = self.apinv_mul(&tw);
        let mut up = f64::INFINITY;
        let mut down = f64::INFINITY;
        for i in 0..p.num_fans {
            let c = clip(f_tau[i], p.fan_min, p.fan_max);
            up = up.min(p.fan_max - c);
            down = down.min(c - p.fan_min);
        }
        let desired_c = wrench[0] / p.num_fans as f64;
        let offset = clip(desired_c, -down, up);
        let mut f = [0.0; NUM_FANS];
        for i in 0..p.num_fans {
            f[i] = f_tau[i] + offset;
        }
        f
    }
}
