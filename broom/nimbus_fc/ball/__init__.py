"""The balls: autonomous Quaffle, Bludger, and Golden Snitch.

Guidance, evasion, and pursuit built on top of accel-limited flying agents,
all sharing one no-contact safety layer. The inner loop that actually realises
a commanded acceleration is the broom's own cascade (nimbus_fc.control).
"""

from . import params
from .avoidance import NoContactAvoidance
from .body import BallBody, Player
from .world import Ball, World

__all__ = ["params", "BallBody", "Player", "World", "Ball", "NoContactAvoidance"]
