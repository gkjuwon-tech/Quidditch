"""NIMBUS-9¾ flight control stack for the manned eVTOL broom.

Public surface is small on purpose; reach into submodules for the internals.
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
