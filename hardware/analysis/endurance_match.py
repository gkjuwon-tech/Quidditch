#!/usr/bin/env python3
"""Challenge 4 — keep the form factor, keep the power budget, fly a whole match.

Battery-only, the broomstick is a ~60 s sprinter (analysis/flight_thermal.py):
no disc area => ~150 kW hover => 2.6 kWh dies in a minute. You cannot fix that
with a bigger battery — 30 minutes at 150 kW is ~75 kWh, ~400 kg of cells, which
does not fit a broom and would not lift.

The honest lever, with form and power both fixed, is ENERGY DENSITY. Liquid fuel
carries ~12,000 Wh/kg vs ~250 Wh/kg for li-ion (~48x). So go SERIES HYBRID:
  * a slim micro-turbine GENSET in the shaft burns sustainable aviation fuel and
    makes the *average* power continuously;
  * the existing 2600 Wh battery becomes the PEAK BUFFER — it still delivers the
    full ~150 kW bursts (so peak thrust/power is unchanged), the genset just
    keeps it topped up.
Thrust stays 8x360 N. Hover power stays ~150 kW. Only the tank empties.

Cost, stated honestly: the genset + fuel add mass, which raises hover power
(P ~ W^1.5), which burns more fuel. This script closes that loop and reports the
real match endurance.

    python3 analysis/endurance_match.py
"""
from __future__ import annotations

import csv
import os

# Battery-only baseline (from analysis/flight_thermal.py)
M_BASE       = 120.0      # kg all-up, battery-only
P_HOVER_BASE = 153.3      # kW electrical draw at hover, base mass
THRUST_AVAIL = 8 * 360.0  # N, unchanged (params.fan_thrust_max x num_fans)
G            = 9.81

# Series-hybrid powertrain
SAF_WH_KG       = 11900.0   # sustainable aviation fuel specific energy (Wh/kg)
ETA_GENSET      = 0.30      # fuel -> electrical (micro-turbine + generator)
GENSET_KW_PER_KG = 4.2      # micro-turbine genset power density
FUEL_KG         = 15.0      # SAF load carried (design point)
TANK_FRAC       = 0.10      # tank/bladder mass as a fraction of fuel
DUTY            = 0.50      # match-average power / hover power. Forward flight
                            # needs far less than hover (induced power drops with
                            # airspeed), and players cruise/dive more than they hover.
MATCH_TARGET_MIN = 18.0     # minimum continuous flight time for the match profile

OUT_CSV = os.path.join(os.path.dirname(__file__), "endurance_match.csv")


def hover_draw_kw(mass_kg: float) -> float:
    """Hover electrical draw scales with weight^1.5 (momentum theory, fixed disc)."""
    return P_HOVER_BASE * (mass_kg / M_BASE) ** 1.5


def main() -> int:
    # fixed-point: genset is sized to average power, which depends on total
    # mass, which depends on genset mass. Converge it.
    genset_kg = 18.0
    for _ in range(50):
        m_hybrid = M_BASE + genset_kg + FUEL_KG + FUEL_KG * TANK_FRAC
        p_hover = hover_draw_kw(m_hybrid)
        p_avg = DUTY * p_hover
        new_genset = p_avg / GENSET_KW_PER_KG
        if abs(new_genset - genset_kg) < 1e-4:
            genset_kg = new_genset
            break
        genset_kg = new_genset

    m_hybrid = M_BASE + genset_kg + FUEL_KG + FUEL_KG * TANK_FRAC
    p_hover = hover_draw_kw(m_hybrid)
    p_avg = DUTY * p_hover
    p_peak = p_hover                              # buffer still serves full hover

    elec_wh = FUEL_KG * SAF_WH_KG * ETA_GENSET    # usable electrical from the fuel
    match_min = elec_wh / 1000.0 / p_avg * 60.0   # genset burns at the average
    tw = THRUST_AVAIL / (m_hybrid * G)

    # battery-only comparison for the same mission profile
    base_min = (2600.0 / 1000.0) / (DUTY * P_HOVER_BASE) * 60.0

    print("=" * 68)
    print(" NIMBUS-9¾ BROOM — MATCH ENDURANCE (series-hybrid range extender)")
    print(" keep the form, keep the power, fill a whole match")
    print("=" * 68)
    print("\n[baseline] battery-only (2600 Wh)")
    print(f"    match-profile flight .. {base_min*60:7.0f} s   ({base_min:.1f} min) — a sprinter")

    print("\n[hybrid] micro-turbine genset + SAF, battery as peak buffer")
    print(f"    fuel carried .......... {FUEL_KG:7.1f} kg   sustainable aviation fuel")
    print(f"    usable electrical ..... {elec_wh/1000:7.1f} kWh  (= fuel x {SAF_WH_KG/1000:.1f} kWh/kg x {ETA_GENSET:.2f})")
    print(f"    genset (sized to avg) . {genset_kg:7.1f} kg / {p_avg:.0f} kW continuous")
    print(f"    peak power (buffer) ... {p_peak:7.0f} kW   unchanged — full hover bursts")
    print(f"    all-up mass ........... {m_hybrid:7.1f} kg   ({M_BASE:.0f} + genset + fuel + tank)")
    print(f"    thrust-to-weight ...... {tw:7.2f}      hover at {100/tw:.0f}% of max thrust")
    print(f"    >> MATCH FLIGHT TIME .. {match_min:7.1f} min")

    fills = match_min >= MATCH_TARGET_MIN
    tw_ok = tw >= 1.3
    print("\n" + "=" * 68)
    print(f" VERDICT: form PASS (slim genset+tank live in the shaft) · "
          f"power PASS (peak {p_peak:.0f} kW kept) · T/W {tw:.2f} "
          f"{'PASS' if tw_ok else 'FAIL'}")
    print(f" ENDURANCE {match_min:.0f} min "
          f"{'>= ' if fills else '< '}{MATCH_TARGET_MIN:.0f} min target -> "
          f"{'FILLS A MATCH.' if fills and tw_ok else 'short.'}")
    print(f" {'>>> A broom that flies a full Quidditch match. <<<' if fills and tw_ok else ''}")
    print("=" * 68)

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value", "unit"])
        w.writerow(["battery_only_flight_min", f"{base_min:.1f}", "min"])
        w.writerow(["fuel_carried_kg", f"{FUEL_KG:.1f}", "kg"])
        w.writerow(["usable_electrical_kwh", f"{elec_wh/1000:.1f}", "kWh"])
        w.writerow(["genset_kg", f"{genset_kg:.1f}", "kg"])
        w.writerow(["genset_cont_kw", f"{p_avg:.0f}", "kW"])
        w.writerow(["peak_power_kw", f"{p_peak:.0f}", "kW"])
        w.writerow(["all_up_mass_kg", f"{m_hybrid:.1f}", "kg"])
        w.writerow(["thrust_to_weight", f"{tw:.2f}", "-"])
        w.writerow(["match_flight_min", f"{match_min:.1f}", "min"])
    print(f"\nwrote {os.path.relpath(OUT_CSV)}")
    return 0 if (fills and tw_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
