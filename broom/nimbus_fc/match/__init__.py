"""Match layer: FC-flown players plus the Dementor referee.

This is where the two halves meet -- the manned-broom flight stack
(nimbus_fc.fc) and the autonomous balls (nimbus_fc.ball) -- inside one
refereed arena.
"""

from . import policies
from .broom_agent import BroomAgent, intent_for_velocity
from .dementor import Dementor

__all__ = ["BroomAgent", "intent_for_velocity", "Dementor", "policies"]
