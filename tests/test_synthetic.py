"""The synthetic primitives must be exactly right — everything else is checked against them."""

from __future__ import annotations

import numpy as np
import pytest

from skyplay.synthetic import bin_curve, fold_phase, fold_time, observe, trapezoid_transit


def test_transit_reaches_full_depth_at_center():
    t = np.array([0.0])
    flux = trapezoid_transit(t, period=10, t0=0.0, duration=0.12, depth=0.01)
    assert flux[0] == pytest.approx(0.99)


def test_transit_is_flat_out_of_transit():
    # A quarter period away from any transit centre.
    t = np.array([2.5, 7.5])
    flux = trapezoid_transit(t, period=10, t0=0.0, duration=0.12, depth=0.01)
    assert np.all(flux == 1.0)


def test_transit_repeats_every_period():
    t = np.linspace(-0.05, 0.05, 51)
    first = trapezoid_transit(t, period=3.5, t0=0.0, duration=0.12, depth=0.01)
    tenth = trapezoid_transit(t + 35.0, period=3.5, t0=0.0, duration=0.12, depth=0.01)
    np.testing.assert_allclose(first, tenth)


def test_ingress_is_halfway_down_at_the_ramp_midpoint():
    duration, depth, ingress_frac = 0.2, 0.01, 0.25
    half, ramp = duration / 2, ingress_frac * duration
    # Midpoint of the ingress ramp should sit at half the full depth.
    flux = trapezoid_transit(np.array([half - ramp / 2]), 10, 0.0, duration, depth, ingress_frac)
    assert flux[0] == pytest.approx(1 - depth / 2)


def test_v_shape_only_touches_full_depth_at_one_point():
    """ingress_frac=0.5 leaves no flat bottom — the mark of a grazing/EB shape."""
    t = np.linspace(-0.1, 0.1, 2001)
    flux = trapezoid_transit(t, 10, 0.0, duration=0.16, depth=0.2, ingress_frac=0.5)
    at_floor = np.isclose(flux, 0.8, atol=1e-6)
    assert at_floor.sum() <= 2


@pytest.mark.parametrize("bad", [0.0, -0.1, 0.6])
def test_rejects_impossible_ingress_fraction(bad):
    with pytest.raises(ValueError, match="ingress_frac"):
        trapezoid_transit(np.array([0.0]), 10, 0.0, 0.1, 0.01, ingress_frac=bad)


def test_fold_time_is_zero_at_every_transit():
    t = np.array([1.3, 1.3 + 3.5, 1.3 + 7.0, 1.3 - 3.5])
    np.testing.assert_allclose(fold_time(t, 3.5, 1.3), 0.0, atol=1e-12)


def test_fold_time_stays_in_half_period_window():
    t = np.linspace(0, 100, 5000)
    folded = fold_time(t, 3.5, 1.3)
    assert folded.min() >= -3.5 / 2 - 1e-12
    assert folded.max() < 3.5 / 2


def test_fold_phase_is_normalized():
    t = np.linspace(0, 100, 5000)
    phase = fold_phase(t, 3.5, 1.3)
    assert phase.min() >= -0.5
    assert phase.max() < 0.5


def test_fold_phase_puts_opposite_side_at_half():
    # Half a period after a transit centre is phase -0.5, which is 0.5 modulo 1.
    assert fold_phase(np.array([1.3 + 1.75]), 3.5, 1.3)[0] == pytest.approx(-0.5)


def test_observe_is_reproducible_from_a_seed():
    base = np.ones(500)
    np.testing.assert_allclose(observe(base, 1e-3, rng=7), observe(base, 1e-3, rng=7))
    assert not np.allclose(observe(base, 1e-3, rng=7), observe(base, 1e-3, rng=8))


def test_observe_has_the_requested_scatter():
    noisy = observe(np.ones(200_000), noise=5e-4, rng=3)
    assert np.std(noisy) == pytest.approx(5e-4, rel=0.02)


def test_bin_curve_averages_within_bins():
    x = np.array([0.1, 0.2, 0.6, 0.7])
    y = np.array([1.0, 3.0, 10.0, 20.0])
    centres, means = bin_curve(x, y, bins=2, range_=(0.0, 1.0))
    np.testing.assert_allclose(centres, [0.25, 0.75])
    np.testing.assert_allclose(means, [2.0, 15.0])


def test_bin_curve_marks_empty_bins_nan():
    """Empty bins must be NaN so plots show a gap instead of interpolating."""
    centres, means = bin_curve(
        np.array([0.05, 0.95]), np.array([1.0, 2.0]), bins=4, range_=(0.0, 1.0)
    )
    assert np.isnan(means[1]) and np.isnan(means[2])
    np.testing.assert_allclose([means[0], means[3]], [1.0, 2.0])
    assert len(centres) == 4


def test_bin_curve_ignores_nan_flux():
    y = np.array([1.0, np.nan, 3.0])
    _, means = bin_curve(np.array([0.1, 0.2, 0.3]), y, bins=1, range_=(0.0, 1.0))
    assert means[0] == pytest.approx(2.0)


def test_binning_reduces_noise_like_sqrt_n():
    """The reason folding works at all: averaging N points cuts scatter by ~sqrt(N)."""
    rng = np.random.default_rng(5)
    x = rng.uniform(0, 1, 60_000)
    y = observe(np.ones(60_000), noise=1e-3, rng=6)
    _, means = bin_curve(x, y, bins=100, range_=(0.0, 1.0))
    expected = 1e-3 / np.sqrt(600)
    assert np.nanstd(means) == pytest.approx(expected, rel=0.25)
