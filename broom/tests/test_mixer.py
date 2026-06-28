"""Tests for thrust allocation in the mixer."""

import numpy as np

from nimbus_fc.control.mixer import Mixer
from nimbus_fc.core.params import Params


def test_hover_allocation_is_even():
    p = Params()
    mix = Mixer(p)
    f, actual = mix.allocate(p.hover_thrust, np.zeros(3))
    assert np.allclose(f, p.hover_thrust / p.num_fans, rtol=1e-6)
    assert np.isclose(actual[0], p.hover_thrust, rtol=1e-6)
    assert np.allclose(actual[1:], 0.0, atol=1e-6)


def test_wrench_roundtrip_in_range():
    p = Params()
    mix = Mixer(p)
    cmd = np.array([2.0, -1.0, 3.0])  # a few small torques
    f, actual = mix.allocate(p.hover_thrust, cmd)
    assert np.all(f >= p.fan_thrust_min - 1e-9)
    assert np.all(f <= p.fan_thrust_max + 1e-9)
    assert np.allclose(actual, [p.hover_thrust, *cmd], atol=1e-6)


def test_saturation_preserves_torque_over_collective():
    p = Params()
    mix = Mixer(p)
    # ask for impossible collective -- torque still has to be honoured
    huge = p.fan_thrust_max * p.num_fans * 2.0
    torque = np.array([0.0, 40.0, 0.0])
    f, actual = mix.allocate(huge, torque)
    assert np.all(f <= p.fan_thrust_max + 1e-9)
    assert np.isclose(actual[2], torque[1], atol=1.0)  # pitch torque survives
