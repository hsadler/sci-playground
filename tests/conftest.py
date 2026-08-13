"""Shared fixtures: synthetic signals whose true parameters we know.

Every test here is offline. Tests that need the archive must be marked
``@pytest.mark.network`` so the suite still runs on a plane.
"""

from __future__ import annotations

import lightkurve as lk
import numpy as np
import pytest

from skyplay.synthetic import KEPLER_LONG_CADENCE, observe, trapezoid_transit

# Ground truth for the fixtures below.
TRUE_PERIOD = 3.5
TRUE_EPOCH = 1.3
TRUE_DURATION = 0.12
TRUE_DEPTH = 0.01
NOISE = 3e-4


@pytest.fixture
def times() -> np.ndarray:
    """60 days at Kepler long cadence."""
    return np.arange(0, 60, KEPLER_LONG_CADENCE)


@pytest.fixture
def planet_flux(times: np.ndarray) -> np.ndarray:
    """A clean transiting planet: flat-bottomed, no secondary eclipse."""
    signal = trapezoid_transit(
        times, TRUE_PERIOD, TRUE_EPOCH, TRUE_DURATION, TRUE_DEPTH, ingress_frac=0.08
    )
    return observe(signal, noise=NOISE, rng=11)


@pytest.fixture
def eclipsing_binary_flux(times: np.ndarray) -> np.ndarray:
    """A V-shaped primary plus a real secondary eclipse at phase 0.5."""
    primary = trapezoid_transit(times, TRUE_PERIOD, TRUE_EPOCH, 0.16, 0.20, ingress_frac=0.5)
    secondary = trapezoid_transit(
        times, TRUE_PERIOD, TRUE_EPOCH + TRUE_PERIOD / 2, 0.16, 0.05, ingress_frac=0.5
    )
    return observe(primary * secondary, noise=NOISE, rng=12)


@pytest.fixture
def alternating_eb_flux(times: np.ndarray) -> np.ndarray:
    """An EB whose true period is 2x TRUE_PERIOD, with unequal alternating eclipses.

    Folded at TRUE_PERIOD — what a period search would report — the deep and shallow
    eclipses land on top of each other. Only the odd-even test separates them.
    """
    true_period = 2 * TRUE_PERIOD
    deep = trapezoid_transit(times, true_period, TRUE_EPOCH, 0.12, 0.020, 0.15)
    shallow = trapezoid_transit(times, true_period, TRUE_EPOCH + true_period / 2, 0.12, 0.010, 0.15)
    return observe(deep * shallow, noise=2e-4, rng=13)


@pytest.fixture
def planet_lc(times: np.ndarray, planet_flux: np.ndarray) -> lk.LightCurve:
    """The planet fixture as a lightkurve `LightCurve`, with uncertainties."""
    return lk.LightCurve(
        time=times,
        flux=planet_flux,
        flux_err=np.full_like(planet_flux, NOISE),
    )
