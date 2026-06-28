"""NIMBUS-9¾ flight control stack for the manned eVTOL broom.

The public surface is small on purpose -- dig into the submodules when you
need the internals.
"""

from .core import (
    CommanderState,
    FlightMode,
    Params,
    RiderIntent,
    State,
)

__version__ = "0.1.0"

__all__ = [
    "Params",
    "State",
    "RiderIntent",
    "FlightMode",
    "CommanderState",
    "__version__",
]
