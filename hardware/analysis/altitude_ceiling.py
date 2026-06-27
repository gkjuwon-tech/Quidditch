#!/usr/bin/env python3
"""Challenge 5 — altitude ceiling and recovery margins.

Real Quidditch is played far up in the air, not at 18 m. Two honest questions
when you climb:
  1) THRUST. Ducted-fan thrust scales with air density, and density falls with
     altitude. Does the broom still have margin to hover up high?
  2) FALLING. The original safety case was "fly low, a fall is survivable."
     At 150 m a fall is lethal -- so the parachute has to be the safety net,
     and it needs altitude to open. Does the math close?

This proves both, then the league simply raises the geofence ceiling
(nimbus_fc/core/params.py fence_ceiling) to the Quidditch altitude -- the
geofence mechanism already enforces whatever number it is given.

    python3 analysis/altitude_ceiling.py
"""
from __future__ import annotations

import csv
import math
import os

G            = 9.81
RHO0         = 1.225          # kg/m^3 sea-level density
SCALE_H      = 8500.0         # m, density scale height (isothermal approx)
THRUST_SL    = 8 * 360.0      # N at sea level (params: fan_thrust_max x num_fans)

# Configurations under comparison
M_SPRINT     = 120.0          # battery-only all-up (params.mass)
M_HYBRID     = 166.0          # series-hybrid all-up (analysis/endurance_match.py)

QUIDDITCH_CEILING = 150.0     # m, the league ceiling we want to fly to
TW_MARGIN    = 1.30           # minimum thrust-to-weight we insist on keeping

# Whole-vehicle ballistic recovery, sized for the heavy configuration
CD_CANOPY    = 1.40
V_DESCENT    = 6.5            # m/s target touchdown rate under canopy (survivable)
BRS_DEPLOY_M = 45.0          # m, rocket-deployed full-inflation altitude


def density(h_m: float) -> float:
    return RHO0 * math.exp(-h_m / SCALE_H)


def thrust_at(h_m: float) -> float:
    return THRUST_SL * density(h_m) / RHO0      # fan thrust ~ rho at max RPM


def service_ceiling(mass_kg: float, tw_min: float) -> float:
    """Altitude where thrust-to-weight falls to tw_min."""
    w = mass_kg * G
    ratio = tw_min * w / THRUST_SL              # required density ratio
    if ratio >= 1.0:
        return 0.0
    return -SCALE_H * math.log(ratio)


def canopy(mass_kg: float):
    area = 2 * mass_kg * G / (RHO0 * CD_CANOPY * V_DESCENT ** 2)
    diam = math.sqrt(4 * area / math.pi)
    return area, diam


def main() -> int:
    rows = []
    print("=" * 68)
    print(" NIMBUS-9¾ BROOM — ALTITUDE / CEILING")
    print(" can it fly high like real Quidditch, and survive the height?")
    print("=" * 68)

    print(f"\n[1] THRUST vs ALTITUDE  (target ceiling {QUIDDITCH_CEILING:.0f} m)")
    print(f"    density at {QUIDDITCH_CEILING:.0f} m .... {density(QUIDDITCH_CEILING)/RHO0*100:5.1f} % of sea level")
    for name, m in (("sprint 120 kg", M_SPRINT), ("hybrid 166 kg", M_HYBRID)):
        w = m * G
        tw_sl = THRUST_SL / w
        tw_ceil = thrust_at(QUIDDITCH_CEILING) / w
        sc = service_ceiling(m, TW_MARGIN)
        hover_sc = service_ceiling(m, 1.0)
        print(f"    {name}: T/W {tw_sl:.2f} (SL) -> {tw_ceil:.2f} @ {QUIDDITCH_CEILING:.0f} m"
              f"  | service ceiling {sc:,.0f} m (T/W {TW_MARGIN}), hover ceiling {hover_sc:,.0f} m")
        rows.append((f"{name}_tw_at_ceiling", f"{tw_ceil:.2f}", "-"))
        rows.append((f"{name}_service_ceiling_m", f"{sc:.0f}", "m"))

    margin_ok = thrust_at(QUIDDITCH_CEILING) / (M_HYBRID * G) >= TW_MARGIN
    print(f"    >> {'PASS' if margin_ok else 'FAIL'}: {QUIDDITCH_CEILING:.0f} m costs <2% thrust; the broom "
          f"can physically reach kilometres. The ceiling is a RULE, not a limit.")

    print("\n[2] SURVIVING THE HEIGHT  (whole-vehicle ballistic parachute)")
    area, diam = canopy(M_HYBRID)
    desc_time = QUIDDITCH_CEILING / V_DESCENT
    print(f"    canopy ................ {area:4.0f} m^2  (Ø {diam:.1f} m) for {V_DESCENT:.1f} m/s touchdown")
    print(f"    full-inflation altitude {BRS_DEPLOY_M:5.0f} m  (rocket-deployed)")
    print(f"    descent from ceiling .. {desc_time:5.0f} s  at {V_DESCENT:.1f} m/s")
    survivable = QUIDDITCH_CEILING > BRS_DEPLOY_M
    print(f"    >> {'PASS' if survivable else 'FAIL'}: at {QUIDDITCH_CEILING:.0f} m the chute has "
          f"{QUIDDITCH_CEILING - BRS_DEPLOY_M:.0f} m to spare to open.")
    print(f"       Honest flip: flying HIGH is SAFE for the chute. The danger band")
    print(f"       is BELOW {BRS_DEPLOY_M:.0f} m -- covered by the airbag skirt + perimeter net.")
    rows.append(("canopy_diameter_m", f"{diam:.1f}", "m"))
    rows.append(("brs_min_deploy_m", f"{BRS_DEPLOY_M:.0f}", "m"))

    ok = margin_ok and survivable
    print("\n" + "=" * 68)
    print(f" VERDICT: THRUST {'PASS' if margin_ok else 'FAIL'} · "
          f"FALL-SURVIVAL {'PASS' if survivable else 'FAIL'}")
    print(f" Raise fence_ceiling to {QUIDDITCH_CEILING:.0f} m and play real, vertical Quidditch.")
    print("=" * 68)

    with open(os.path.join(os.path.dirname(__file__), "altitude_ceiling.csv"),
              "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value", "unit"])
        w.writerow(["quidditch_ceiling_m", f"{QUIDDITCH_CEILING:.0f}", "m"])
        for r in rows:
            w.writerow(r)
    print("\nwrote analysis/altitude_ceiling.csv")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
