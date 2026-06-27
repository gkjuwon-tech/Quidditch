"""Battery model: energy drawn as a function of mechanical power demand.

Crude but honest: electrical power = mechanical power / efficiency, where
mechanical power scales with thrust^1.5 (momentum theory, P ~ T*v_induced and
v_induced ~ sqrt(T)). good enough to make "Return To Pit" a real consequence of
flying hard, which is the whole point for the demo.
"""

from __future__ import annotations

from ..core.math3d import GRAVITY
from ..core.params import Params


class Battery:
    def __init__(self, params: Params, initial_soc: float = 1.0):
        self.p = params
        self.energy_wh = params.batt_capacity_wh * initial_soc
        # calibrate the power constant so hovering hits the rated efficiency.
        # P_hover_electrical implied by batt_hover_eta at hover thrust: treat
        # hover induced power as T*sqrt(T/(2*rho*A)); fold all the
        # disc-area/rho constants into one k calibrated at hover.
        hover_T = params.hover_thrust
        p_mech_hover = hover_T ** 1.5
        self._k = (hover_T * 9.0) / (params.batt_hover_eta * p_mech_hover)
        # (the 9.0 sets a ~few-minute endurance scale for a 2.6 kWh pack)

    @property
    def soc(self) -> float:
        return max(0.0, self.energy_wh / self.p.batt_capacity_wh)

    @property
    def empty(self) -> bool:
        return self.energy_wh <= 0.0

    def electrical_power_w(self, total_thrust_n: float) -> float:
        t = max(total_thrust_n, 0.0)
        return self._k * (t ** 1.5)

    def update(self, total_thrust_n: float, dt: float) -> None:
        power_w = self.electrical_power_w(total_thrust_n)
        self.energy_wh -= power_w * (dt / 3600.0)
        if self.energy_wh < 0.0:
            self.energy_wh = 0.0
