"""nimbus_hal — the bridge between the flight software and the physical broom.

The flight stack (nimbus_fc) ends at the MIXER, which emits a per-fan thrust
command in NEWTONS (one per fan, params.num_fans). This module turns those
commands into what the hardware actually wants — DShot throttle frames to the
ESCs — and turns the raw sensors back into the state the estimator expects.
It also carries the THERMAL GOVERNOR: the one extra loop a bare-stick airframe
needs, which derates thrust before the in-shaft motors cook.

Runtime split (see broom/README.md):
  * the hard real-time cascade (pos->att->rate->mixer) is the Rust core
    (rust/nimbus_core) on the Cortex-M4F;
  * this HAL is the I/O skin around it — protocols, scaling, limits, thermal.

Pure-stdlib and importable on a host for SITL; the same logic is mirrored in
firmware C against the pin map in firmware/pinmap.csv.

    python3 firmware/hal.py        # self-test: prints a command/telemetry frame
"""
from __future__ import annotations

from dataclasses import dataclass, field

# --- mirrors nimbus_fc/core/params.py (single source of truth there) -----
NUM_FANS       = 8
FAN_THRUST_MAX = 360.0     # N at full throttle           (params.fan_thrust_max)
FAN_TAU        = 0.04      # s, 1st-order thrust response  (params.fan_tau)

# --- DShot ----------------------------------------------------------------
DSHOT_MIN      = 48        # 0..47 are reserved commands; 48 = 0% throttle
DSHOT_MAX      = 2047

# --- thermal governor knobs ----------------------------------------------
T_WARN_C       = 105.0     # start derating windings here
T_MAX_C        = 120.0     # hard winding limit -> floor authority
DERATE_FLOOR   = 0.55      # never derate below this (you're carrying a person)


def thrust_to_throttle(thrust_n: float) -> float:
    """Newtons -> 0..1 throttle. EDF thrust ~ throttle^2, so invert that."""
    frac = max(0.0, min(1.0, thrust_n / FAN_THRUST_MAX))
    return frac ** 0.5


def throttle_to_dshot(throttle: float) -> int:
    throttle = max(0.0, min(1.0, throttle))
    return int(round(DSHOT_MIN + throttle * (DSHOT_MAX - DSHOT_MIN)))


def thermal_derate(temp_c: float) -> float:
    """Per-fan authority multiplier from winding temperature."""
    if temp_c <= T_WARN_C:
        return 1.0
    if temp_c >= T_MAX_C:
        return DERATE_FLOOR
    span = (temp_c - T_WARN_C) / (T_MAX_C - T_WARN_C)
    return 1.0 - span * (1.0 - DERATE_FLOOR)


@dataclass
class FanState:
    thrust_n: float = 0.0       # slew-limited actual thrust estimate
    temp_c: float = 30.0        # winding temperature from the in-duct sensor


@dataclass
class HAL:
    """Stateless-ish I/O skin: feed it mixer thrusts + sensor temps, get back
    the DShot frame the ESCs receive and a telemetry snapshot."""
    dt: float = 0.0025          # 400 Hz, matches params.dt
    fans: list = field(default_factory=lambda: [FanState() for _ in range(NUM_FANS)])
    governor_active: bool = False

    def step(self, thrust_cmd_n, temps_c):
        """One control tick.
        thrust_cmd_n: list[NUM_FANS] commanded thrust (N) straight from the mixer
        temps_c:      list[NUM_FANS] measured winding temps (deg C)
        returns:      (dshot[NUM_FANS], telemetry dict)
        """
        assert len(thrust_cmd_n) == NUM_FANS and len(temps_c) == NUM_FANS
        dshot, applied = [], []
        self.governor_active = False
        alpha = self.dt / (FAN_TAU + self.dt)     # 1st-order response, params.fan_tau
        for i, (cmd, temp) in enumerate(zip(thrust_cmd_n, temps_c)):
            k = thermal_derate(temp)
            if k < 1.0:
                self.governor_active = True
            cmd_lim = max(0.0, min(FAN_THRUST_MAX * k, cmd))
            # model the fan's finite response so SITL matches the airframe
            f = self.fans[i]
            f.thrust_n += alpha * (cmd_lim - f.thrust_n)
            f.temp_c = temp
            dshot.append(throttle_to_dshot(thrust_to_throttle(cmd_lim)))
            applied.append(cmd_lim)
        telem = dict(
            dshot=dshot,
            applied_thrust_n=[round(a, 1) for a in applied],
            actual_thrust_n=[round(f.thrust_n, 1) for f in self.fans],
            temps_c=list(temps_c),
            hottest_c=max(temps_c),
            governor_active=self.governor_active,
            total_thrust_n=round(sum(applied), 1),
        )
        return dshot, telem


def _demo():
    hal = HAL()
    # mixer asks for hover-ish thrust; it demands a hard pull from fan 3 right
    # as fan 3 runs hot, so the governor has to bite and clamp it.
    cmd = [150.0, 150.0, 150.0, 320.0, 150.0, 150.0, 150.0, 150.0]
    temps = [60.0, 62.0, 59.0, 113.0, 58.0, 61.0, 60.0, 57.0]   # fan 3 is cooking
    dshot, telem = hal.step(cmd, temps)
    print("nimbus_hal self-test  (8 fans, one at 113 C)")
    print(f"  commanded thrust : {cmd[0]:.0f} N each")
    print(f"  DShot frame      : {dshot}")
    print(f"  applied thrust   : {telem['applied_thrust_n']}  N")
    print(f"  hottest winding  : {telem['hottest_c']:.0f} C")
    print(f"  governor active  : {telem['governor_active']}  "
          f"(fan 3 derated to {thermal_derate(113.0)*100:.0f}% authority)")
    print(f"  total thrust     : {telem['total_thrust_n']:.0f} N "
          f"(weight to beat: 1177 N)")


if __name__ == "__main__":
    _demo()
