"""The balls: autonomous Quaffle, Bludger, and Golden Snitch.

Guidance/evasion/pursuit on top of acceleration-limited flying agents, with a
shared no-contact safety layer. The inner flight control that realises a
commanded acceleration is the broom's proven cascade (nimbus_fc.control).
"""

from . import params
from .avoidance import NoContactAvoidance
from .body import BallBody, Player
from .world import Ball, World

__all__ = ["params", "BallBody", "Player", "World", "Ball", "NoContactAvoidance"]
