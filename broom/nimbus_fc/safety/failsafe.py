"""Failsafe policy: battery + datalink in, a recommended safe action out.

No state machine lives here. The commander owns transitions and just asks
this "given the hazards right now, what should I do". Battery uses the same
two-stage low/critical idea as ArduPilot, and the link check is debounced so
one dropped packet doesn't send us home.
"""

from __future__ import annotations

from enum import Enum

from ..core.params import Params


class FailsafeAction(str, Enum):
    NONE = "NONE"
    RETURN_TO_PIT = "RETURN_TO_PIT"   # battery low or link dropped
    LAND_NOW = "LAND_NOW"             # battery critical, just put it down


class Failsafe:
    def __init__(self, params: Params, link_timeout: float = 1.5):
        self.p = params
        self.link_timeout = link_timeout
        self._link_lost_for = 0.0

    def evaluate(self, soc: float, link_ok: bool, dt: float) -> tuple[FailsafeAction, str]:
        # accumulate time-without-link, reset the instant a packet gets through
        self._link_lost_for = 0.0 if link_ok else self._link_lost_for + dt

        if soc <= self.p.batt_land_soc:
            return FailsafeAction.LAND_NOW, f"battery critical ({soc*100:.0f}%) - landing now"
        if soc <= self.p.batt_rtp_soc:
            return FailsafeAction.RETURN_TO_PIT, f"battery low ({soc*100:.0f}%) - returning to pit"
        if self._link_lost_for >= self.link_timeout:
            return FailsafeAction.RETURN_TO_PIT, "datalink lost - returning to pit"
        return FailsafeAction.NONE, ""
