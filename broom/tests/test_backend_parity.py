"""the Rust core must reproduce the Python reference, tick for tick.

A polyglot safety core is only trustworthy if the compiled path is provably the
same behaviour as the readable reference. we fly identical scenarios on both
backends and require the trajectories to match to floating-point noise.

Skipped automatically if the Rust cdylib hasn't been built.
"""

import numpy as np
import pytest

from nimbus_fc.control.backend import rust_available
from nimbus_fc.core.types import RiderIntent, State
from nimbus_fc.safety.commander import Commands
from nimbus_fc.sim.rider import RiderScript, Segment
from nimbus_fc.sim.simulator import Simulator

pytestmark = pytest.mark.skipif(
    not rust_available(),
    reason="rust core not built (cd rust/nimbus_core && cargo build --release)")


def _fly(backend: str):
    sim = Simulator(initial=State(pos=np.array([0.0, 0.0, 0.0])), backend=backend)
    script = RiderScript([
        Segment(0.0, cmd=Commands(arm=True)),
        Segment(0.5, cmd=Commands(takeoff=True)),
        Segment(7.0, intent=RiderIntent(pitch=0.7, roll=0.4)),
        Segment(14.0, intent=RiderIntent(yaw=0.5, lift=0.4)),
        Segment(20.0, intent=RiderIntent()),
    ])
    sim.run(28.0, lambda t, s: script(t))
    return np.array([[r["x"], r["y"], r["z"], r["yaw"], r["pitch"], r["roll"]]
                     for r in sim.log.rows])


def test_rust_matches_python_trajectory():
    py = _fly("python")
    ru = _fly("rust")
    assert py.shape == ru.shape
    max_diff = np.abs(py - ru).max()
    assert max_diff < 1e-6, f"backends diverged: max |diff| = {max_diff:.2e}"


def test_rust_geofence_containment():
    """the safety property must hold identically on the Rust core."""
    sim = Simulator(initial=State(pos=np.array([0.0, 0.0, 0.0])), backend="rust")
    script = RiderScript([
        Segment(0.0, cmd=Commands(arm=True)),
        Segment(0.5, cmd=Commands(takeoff=True)),
        Segment(8.0, intent=RiderIntent(pitch=1.0, roll=1.0)),
    ])
    sim.run(45.0, lambda t, s: script(t))
    for r in sim.log.rows:
        assert -50.0 <= r["x"] <= 50.0 and -25.0 <= r["y"] <= 25.0
