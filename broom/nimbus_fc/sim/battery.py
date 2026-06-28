"""A small battery model: energy out as a function of power demand.

Crude but not dishonest. Electrical power = mechanical / efficiency, and
mechanical power goes like thrust^1.5 (momentum theory: P ~ T*v_induced,
v_induced ~ sqrt(T)). That's enough to make Return-To-Pit an actual
consequence of flying hard, which is all the demo needs.
"""

from __future__ import annotations

from ..core.params import Params


class Battery:
    def __init__(self, params: Params, initial_soc: float = 1.0):
        self.p = params
        self.energy_wh = params.batt_capacity_wh * initial_soc
        # pin the power constant so hover lands exactly on the rated efficiency.
        hover_T = params.hover_thrust
        # induced hover power is ~ T*sqrt(T/(2*rho*A)); roll the rho and disc
        # area into one k and calibrate it at the hover point.
        p_mech_hover = hover_T ** 1.5
        self._k = (hover_T * 9.0) / (params.batt_hover_eta * p_mech_hover)
        # the 9.0 just sets a few-minute endurance for a 2.6 kWh pack

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
