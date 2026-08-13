"""The vetting checks must actually reject the impostors they claim to reject.

These are the highest-value tests in the repo: a vetting function that silently
passes everything would make every later "discovery" worthless.
"""

from __future__ import annotations

import numpy as np
import pytest

from skyplay.vetting import (
    MAX_PLANETARY_RP_RS,
    dilute_depth,
    measure_depth,
    odd_even_depths,
    secondary_eclipse_depth,
    vet,
)

from .conftest import TRUE_DEPTH, TRUE_EPOCH, TRUE_PERIOD


def test_measures_the_injected_depth(times, planet_flux):
    from skyplay.synthetic import fold_phase

    phase = fold_phase(times, TRUE_PERIOD, TRUE_EPOCH)
    depth = measure_depth(phase, planet_flux, center=0.0, halfwidth=0.01)
    assert depth == pytest.approx(TRUE_DEPTH, rel=0.05)


def test_planet_has_no_secondary_eclipse(times, planet_flux):
    depth = secondary_eclipse_depth(times, planet_flux, TRUE_PERIOD, TRUE_EPOCH)
    # Consistent with zero at this noise level.
    assert abs(depth) < 1e-3


def test_eclipsing_binary_shows_a_secondary_eclipse(times, eclipsing_binary_flux):
    depth = secondary_eclipse_depth(times, eclipsing_binary_flux, TRUE_PERIOD, TRUE_EPOCH)
    # The injected secondary is 5% deep at its floor, but it is V-shaped, so a
    # *median* over the eclipse window lands well below the peak — a real effect to
    # keep in mind when reading these numbers. What matters is that it is
    # unambiguously present, orders of magnitude above the planet case below.
    assert depth > 0.02


def test_secondary_eclipse_detection_separates_planet_from_binary(
    times, planet_flux, eclipsing_binary_flux
):
    planet = secondary_eclipse_depth(times, planet_flux, TRUE_PERIOD, TRUE_EPOCH)
    binary = secondary_eclipse_depth(times, eclipsing_binary_flux, TRUE_PERIOD, TRUE_EPOCH)
    assert binary > 20 * abs(planet)


def test_planet_odd_and_even_depths_agree(times, planet_flux):
    even, odd = odd_even_depths(times, planet_flux, TRUE_PERIOD, TRUE_EPOCH, halfwidth=0.01)
    assert even == pytest.approx(odd, rel=0.1)


def test_alternating_binary_odd_and_even_depths_disagree(times, alternating_eb_flux):
    """Folded at half the true period, the two eclipse depths must not match."""
    even, odd = odd_even_depths(times, alternating_eb_flux, TRUE_PERIOD, TRUE_EPOCH, halfwidth=0.01)
    mismatch = abs(even - odd) / max(even, odd)
    assert mismatch > 0.25


def test_measure_depth_window_wraps_around_phase_boundary():
    """Phase is cyclic: a window centred on 0.5 must collect points near -0.5 too."""
    phase = np.array([-0.499, 0.499, 0.25, -0.25])
    flux = np.array([0.9, 0.9, 1.0, 1.0])
    assert measure_depth(phase, flux, center=0.5, halfwidth=0.02) == pytest.approx(0.1)


def test_measure_depth_returns_nan_for_an_empty_window():
    phase = np.array([0.25, -0.25])
    assert np.isnan(measure_depth(phase, flux=np.array([1.0, 1.0]), center=0.0, halfwidth=0.001))


def test_dilution_makes_a_stellar_eclipse_look_planetary():
    """The contamination trap: a 9% eclipse behind a 3x brighter neighbour reads as 2%."""
    true_depth = 0.09
    measured = dilute_depth(true_depth, neighbor_flux_ratio=3.0)

    assert measured == pytest.approx(0.0225)
    # Undiluted, the radius ratio is far too large to be a planet...
    assert np.sqrt(true_depth) > MAX_PLANETARY_RP_RS
    # ...but after dilution it slips under a naive radius cut.
    assert np.sqrt(measured) < MAX_PLANETARY_RP_RS


def test_no_dilution_is_the_identity():
    assert dilute_depth(0.01, 0.0) == pytest.approx(0.01)


def test_dilution_rejects_negative_ratio():
    with pytest.raises(ValueError):
        dilute_depth(0.01, -1.0)


def test_report_passes_a_real_planet(times, planet_flux):
    report = vet(times, planet_flux, TRUE_PERIOD, TRUE_EPOCH, halfwidth=0.01)
    assert report.passed, report.summary()
    assert report.rp_rs == pytest.approx(0.1, rel=0.05)


def test_report_rejects_an_eclipsing_binary(times, eclipsing_binary_flux):
    report = vet(times, eclipsing_binary_flux, TRUE_PERIOD, TRUE_EPOCH, halfwidth=0.01)
    assert not report.passed
    checks = report.checks()
    assert not checks["no secondary eclipse"][0]
    # A 20% eclipse also implies Rp/Rs ~ 0.45, far too big for a planet.
    assert not checks["radius is planetary"][0]


def test_report_rejects_an_alternating_binary_on_odd_even(times, alternating_eb_flux):
    report = vet(times, alternating_eb_flux, TRUE_PERIOD, TRUE_EPOCH, halfwidth=0.01)
    assert not report.passed
    assert not report.checks()["odd/even depths agree"][0]


def test_summary_mentions_every_check(times, planet_flux):
    report = vet(times, planet_flux, TRUE_PERIOD, TRUE_EPOCH, halfwidth=0.01)
    text = report.summary()
    for name in report.checks():
        assert name in text
