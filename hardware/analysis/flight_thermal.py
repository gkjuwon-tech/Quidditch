#!/usr/bin/env python3
"""NIMBUS broom — flight + thermal budget flight and thermal budget.

A bare broomstick has almost no disc area, so the honest questions are:
  1) can 8 ducted fans even lift a 120 kg rider+airframe? (thrust budget)
  2) how long before the battery dies? (endurance — a broom is a sprinter)
  3) do the motors melt inside a thin shaft? (thermal budget)

This computes all three from first principles, using the SAME numbers the
flight software flies with (nimbus_fc/core/params.py), and prints a PASS/FAIL
report. The key trick for (3): the lift air IS the coolant — the motors sit
in the duct flow, and heat pipes spread the rest over the 2.4 m shaft.

    python3 analysis/flight_thermal.py        # report -> stdout + CSV
"""
from __future__ import annotations

import csv
import math
import os

# Inputs, mirrored from nimbus_fc/core/params.py
G            = 9.81
MASS         = 120.0          # kg, rider ~80 + airframe ~40   (params.mass)
N_FANS       = 8              # params.num_fans (_default_fan_layout)
T_MAX_FAN    = 360.0          # N, params.fan_thrust_max  (cluster T/W ~2.4)
BATT_WH      = 2600.0         # params.batt_capacity_wh
RTP_SOC      = 0.30           # params.batt_rtp_soc  (forced pit at 30%)

# Airframe geometry (hardware/cad/broom.scad)
# Constraint: the disc must fit entirely inside the visible silhouette,
# so the main fan is sized to nest within the bristle flare at its widest (it
# does not protrude in any non-cutaway view). The flare frontal area is the
# disc-area ceiling -- the packaging cost of keeping the broom silhouette.
D_MAIN       = 0.34          # m, main lift fan, fits inside the bristle leaf
D_SHAFT_FAN  = 0.055         # m, each of the in-shaft trim/attitude fans
N_SHAFT_FAN  = 8

# Efficiencies / environment
RHO          = 1.225         # kg/m^3 air
FM           = 0.62          # ducted-fan figure of merit (ducts beat open props)
ETA_MOTOR    = 0.88
ETA_ESC      = 0.96
ETA_WIRING   = 0.97
CP_AIR       = 1005.0        # J/kg/K
DT_COOLANT   = 25.0          # K allowable air temperature rise through the duct
T_AMBIENT    = 30.0          # deg C design-day
T_MOTOR_MAX  = 120.0         # deg C winding limit (derate target below this)

OUT_CSV = os.path.join(os.path.dirname(__file__), "flight_thermal.csv")


def disc_area() -> float:
    a_main = math.pi / 4 * D_MAIN ** 2
    a_shaft = N_SHAFT_FAN * math.pi / 4 * D_SHAFT_FAN ** 2
    return a_main + a_shaft


def main() -> int:
    rows = []
    def line(label, value, unit="", verdict=""):
        rows.append((label, value, unit, verdict))

    W = MASS * G
    T_avail = N_FANS * T_MAX_FAN
    tw = T_avail / W
    hover_frac = W / T_avail

    A = disc_area()
    DL = W / A                                   # disc loading, N/m^2
    v_i = math.sqrt(DL / (2 * RHO))              # induced velocity at the disc
    v_exh = 2 * v_i
    mdot = RHO * A * v_i                          # air mass flow

    P_ideal = W ** 1.5 / math.sqrt(2 * RHO * A)  # momentum-theory hover power
    P_shaft = P_ideal / FM
    P_elec = P_shaft / (ETA_MOTOR * ETA_ESC)
    P_draw = P_elec / ETA_WIRING                 # battery draw at hover

    Q_waste = P_draw - P_shaft                   # everything not in the airstream
    cool_cap = mdot * CP_AIR * DT_COOLANT        # through-flow cooling capacity
    cool_margin = cool_cap / Q_waste

    endur_full = BATT_WH / P_draw * 3600.0               # s, to empty (P_draw in W)
    endur_pit = BATT_WH * (1 - RTP_SOC) / P_draw * 3600.0  # s, to forced RTP

    print("=" * 68)
    print(" NIMBUS-9¾ BROOM — FLIGHT + THERMAL BUDGET")
    print(" (a thin stick that has to carry a person, honestly)")
    print("=" * 68)

    print("\n[1] THRUST — can a broomstick lift a person?")
    print(f"    all-up weight ......... {W:8.0f} N   ({MASS:.0f} kg)")
    print(f"    thrust available ...... {T_avail:8.0f} N   ({N_FANS} x {T_MAX_FAN:.0f} N)")
    print(f"    thrust-to-weight ...... {tw:8.2f}     hover at {hover_frac*100:.0f}% throttle")
    flight_ok = tw >= 1.3
    print(f"    >> {'PASS' if flight_ok else 'FAIL'}: hovers with margin; spends the rest on control authority")
    line("thrust_to_weight", f"{tw:.2f}", "-", "PASS" if flight_ok else "FAIL")
    line("hover_throttle", f"{hover_frac*100:.0f}", "%")

    print("\n[2] DISC + power budget — the brutal cost of having no disc area")
    print(f"    effective disc area ... {A*1e4:8.0f} cm^2  (bristle shroud + shaft fans)")
    print(f"    disc loading .......... {DL/1000:8.1f} kPa   (helicopters live near 0.5)")
    print(f"    exhaust velocity ...... {v_exh:8.0f} m/s")
    print(f"    ideal hover power ..... {P_ideal/1000:8.1f} kW")
    print(f"    electrical draw ....... {P_draw/1000:8.1f} kW")
    line("disc_loading_kpa", f"{DL/1000:.1f}", "kPa")
    line("hover_draw_kw", f"{P_draw/1000:.1f}", "kW")

    print("\n[3] ENDURANCE — a broom is a sprinter, not a marathoner")
    print(f"    usable battery ........ {BATT_WH:8.0f} Wh")
    print(f"    hover to empty ........ {endur_full:8.0f} s   ({endur_full/60:.1f} min)")
    print(f"    hover to forced pit ... {endur_pit:8.0f} s   ({endur_pit/60:.1f} min, at {RTP_SOC*100:.0f}% SoC)")
    print(f"    >> BY DESIGN it's a ~{endur_full/60:.1f}-min sprinter: no disc area = high power.")
    print(f"       The league runs F1-style hot-swap PITS, and nimbus_fc already")
    print(f"       forces Return-To-Pit at {RTP_SOC*100:.0f}% SoC. The shape costs endurance; we pit.")
    line("endurance_to_pit_s", f"{endur_pit:.0f}", "s")

    print("\n[4] THERMAL — does the stick melt? (the real 궁지)")
    print(f"    waste heat at hover ... {Q_waste/1000:8.1f} kW   (motor + ESC + wiring losses)")
    print(f"    duct air mass flow .... {mdot:8.1f} kg/s")
    print(f"    air-cooling capacity .. {cool_cap/1000:8.1f} kW   (= mdot x cp x {DT_COOLANT:.0f}K)")
    print(f"    cooling margin ........ {cool_margin:8.1f} x   over waste heat")
    therm_ok = cool_margin >= 3.0
    print(f"    >> {'PASS' if therm_ok else 'FAIL'}: the lift air IS the coolant. Motors live in the")
    print(f"       duct flow; heat pipes spread the rest over the 2.4 m shaft.")
    print(f"       Governor derates thrust above {T_MOTOR_MAX:.0f}C winding temp (firmware/hal.py).")
    line("waste_heat_kw", f"{Q_waste/1000:.1f}", "kW")
    line("cooling_margin_x", f"{cool_margin:.1f}", "x", "PASS" if therm_ok else "FAIL")

    overall = flight_ok and therm_ok
    print("\n" + "=" * 68)
    print(f" VERDICT: FLIGHT {'PASS' if flight_ok else 'FAIL'} · "
          f"THERMAL {'PASS' if therm_ok else 'FAIL'} · "
          f"ENDURANCE short-by-design (pit doctrine)")
    print(f" {'>>> THE BUDGET CLOSES. The broom flies, and it does not melt. <<<' if overall else '>>> does not close <<<'}")
    print("=" * 68)

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value", "unit", "verdict"])
        for r in rows:
            w.writerow(r)
    print(f"\nwrote {os.path.relpath(OUT_CSV)}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
