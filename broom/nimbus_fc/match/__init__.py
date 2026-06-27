"""Match layer: flight-controller-backed players + the Dementor central referee.

Brings the two halves together -- the manned-broom flight stack (nimbus_fc.fc)
and the autonomous balls (nimbus_fc.ball) -- into one refereed arena.
"""

from . import policies
from .broom_agent import BroomAgent, intent_for_velocity
from .dementor import Dementor

__all__ = ["BroomAgent", "intent_for_velocity", "Dementor", "policies"]
