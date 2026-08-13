"""Period search, detrending, caching, and the batman model.

The recurring assertion: given a signal we injected, does the machinery recover the
parameters we put in?
"""

from __future__ import annotations

import numpy as np
import pytest

from skyplay import cache, detrend, models, periods
from skyplay.synthetic import KEPLER_LONG_CADENCE, observe, trapezoid_transit

from .conftest import NOISE, TRUE_DEPTH, TRUE_DURATION, TRUE_EPOCH, TRUE_PERIOD

# ---------------------------------------------------------------- period search


def test_bls_recovers_the_injected_period(planet_lc):
    found = periods.bls_search(planet_lc, period_min=2, period_max=6, n_periods=4000)
    assert found.period == pytest.approx(TRUE_PERIOD, rel=0.01)
    assert found.method == "BLS"


def test_bls_recovers_the_injected_depth(planet_lc):
    found = periods.bls_search(planet_lc, period_min=2, period_max=6, n_periods=4000)
    assert found.depth == pytest.approx(TRUE_DEPTH, rel=0.15)
    assert found.rp_rs == pytest.approx(0.1, rel=0.1)


def test_bls_epoch_lands_on_a_real_transit(planet_lc):
    found = periods.bls_search(planet_lc, period_min=2, period_max=6, n_periods=4000)
    # The recovered epoch should be an integer number of periods from the truth.
    offset = (found.epoch - TRUE_EPOCH) / TRUE_PERIOD
    assert abs(offset - round(offset)) < 0.05


def test_default_thread_count_leaves_the_machine_usable():
    """TLS's own default is every core, which cooks a laptop. Ours must not be.

    This guards a real incident: an unbounded TLS search saturated all 12 threads.
    """
    import os

    cores = os.cpu_count() or 1
    assert 1 <= periods.DEFAULT_THREADS <= 4
    if cores > 2:
        assert periods.DEFAULT_THREADS <= cores - 2


def test_tls_recovers_the_injected_period(planet_lc):
    found = periods.tls_search(planet_lc, period_min=3, period_max=4, use_threads=1)
    assert found.period == pytest.approx(TRUE_PERIOD, rel=0.01)
    assert found.power_label == "SDE"


def test_tls_depth_is_converted_to_a_dip_not_a_floor_level(planet_lc):
    """TLS reports the floor level (~0.99); our wrapper must return the dip (~0.01)."""
    found = periods.tls_search(planet_lc, period_min=3, period_max=4, use_threads=1)
    assert found.depth == pytest.approx(TRUE_DEPTH, rel=0.2)
    assert found.depth < 0.5, "depth looks like a floor level, not a dip"


def test_tls_reports_a_strong_detection_for_an_obvious_transit(planet_lc):
    found = periods.tls_search(planet_lc, period_min=3, period_max=4, use_threads=1)
    assert found.power > 9  # SDE well past the usual significance threshold


def test_search_result_exposes_a_usable_spectrum(planet_lc):
    found = periods.bls_search(planet_lc, period_min=2, period_max=6, n_periods=2000)
    assert found.periods.shape == found.spectrum.shape
    # The peak of the spectrum must be at the reported period.
    assert found.periods[np.argmax(found.spectrum)] == pytest.approx(found.period)


def test_compare_to_formats_the_disagreement(planet_lc):
    found = periods.bls_search(planet_lc, period_min=2, period_max=6, n_periods=2000)
    assert "% off" in found.compare_to(TRUE_PERIOD)


# ------------------------------------------------------------------- detrending


@pytest.fixture
def trending_lc():
    """A transit riding on a slow sinusoidal trend, as a spotted star would give."""
    import lightkurve as lk

    t = np.arange(0, 60, KEPLER_LONG_CADENCE)
    transit = trapezoid_transit(t, TRUE_PERIOD, TRUE_EPOCH, TRUE_DURATION, TRUE_DEPTH, 0.08)
    trend = 1.0 + 0.02 * np.sin(2 * np.pi * t / 12.0)  # 2%, 12-day period
    flux = observe(transit * trend, noise=NOISE, rng=21)
    return lk.LightCurve(time=t, flux=flux, flux_err=np.full_like(flux, NOISE))


def test_cadence_is_detected(trending_lc):
    assert detrend.cadence_days(trending_lc) == pytest.approx(KEPLER_LONG_CADENCE)


def test_days_convert_to_an_odd_cadence_count(trending_lc):
    n = detrend.days_to_cadences(trending_lc, 18.8)
    assert n % 2 == 1
    assert n == pytest.approx(901, abs=2)  # matches the notebooks' window_length=901


def test_biweight_removes_the_trend(trending_lc):
    flat, trend = detrend.biweight_flatten(trending_lc, window_days=0.5)
    # Out-of-transit scatter should collapse to roughly the injected noise.
    assert np.nanstd(flat.flux.value) < np.nanstd(trending_lc.flux.value) / 4
    assert np.nanmedian(trend.flux.value) == pytest.approx(1.0, abs=0.03)


def test_biweight_preserves_transit_depth(trending_lc):
    """The whole point of a robust filter: it must not eat the signal."""
    from skyplay.vetting import vet

    flat, _ = detrend.biweight_flatten(trending_lc, window_days=0.5)
    report = vet(flat.time.value, flat.flux.value, TRUE_PERIOD, TRUE_EPOCH, halfwidth=0.01)
    assert report.transit_depth == pytest.approx(TRUE_DEPTH, rel=0.15)


def test_savgol_also_recovers_the_period(trending_lc):
    flat, _ = detrend.savgol_flatten(trending_lc, window_days=18.8)
    found = periods.bls_search(flat.remove_nans(), period_min=2, period_max=6, n_periods=3000)
    assert found.period == pytest.approx(TRUE_PERIOD, rel=0.01)


def test_sigma_clipping_is_what_protects_savgol_from_eating_the_transit(trending_lc):
    """lightkurve's `flatten` clips outliers before fitting, and in-transit points are
    outliers — so it survives a window it has no business surviving. Disabling the
    clipping exposes the real failure mode."""
    from skyplay.vetting import vet

    def depth_with(**kwargs):
        flat, _ = detrend.savgol_flatten(trending_lc, window_days=TRUE_DURATION, **kwargs)
        return vet(
            flat.time.value, flat.flux.value, TRUE_PERIOD, TRUE_EPOCH, halfwidth=0.01
        ).transit_depth

    clipped = depth_with()
    unclipped = depth_with(niters=1, sigma=1e9)
    assert unclipped < clipped / 2, (clipped, unclipped)


def test_too_narrow_a_window_destroys_the_transit(trending_lc):
    """Documents the failure mode: a window near the transit duration absorbs it."""
    from skyplay.vetting import vet

    flat, _ = detrend.biweight_flatten(trending_lc, window_days=TRUE_DURATION)
    report = vet(flat.time.value, flat.flux.value, TRUE_PERIOD, TRUE_EPOCH, halfwidth=0.01)
    assert report.transit_depth < TRUE_DEPTH / 2


# ------------------------------------------------------------------------ cache


def test_lightcurve_survives_a_cache_round_trip(planet_lc, tmp_path):
    path = cache.save_lightcurve(planet_lc, tmp_path / "rt.parquet")
    back = cache.load_lightcurve(path)

    np.testing.assert_allclose(back.time.value, planet_lc.time.value)
    np.testing.assert_allclose(back.flux.value, planet_lc.flux.value)
    np.testing.assert_allclose(back.flux_err.value, planet_lc.flux_err.value)
    assert back.time.format == planet_lc.time.format
    assert back.time.scale == planet_lc.time.scale


def test_cached_builds_once_then_reads_from_disk(planet_lc, tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "cache_dir", lambda: tmp_path)
    calls = []

    def build():
        calls.append(1)
        return planet_lc

    first = cache.cached("k", build)
    second = cache.cached("k", build)
    assert len(calls) == 1
    np.testing.assert_allclose(first.flux.value, second.flux.value)


def test_refresh_forces_a_rebuild(planet_lc, tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "cache_dir", lambda: tmp_path)
    calls = []

    def build():
        calls.append(1)
        return planet_lc

    cache.cached("k", build)
    cache.cached("k", build, refresh=True)
    assert len(calls) == 2


# ------------------------------------------------------------- batman modelling


def test_batman_transit_is_deeper_than_the_radius_ratio_squared():
    """Limb darkening makes the central depth exceed (Rp/Rs)**2. Worth pinning down."""
    t = np.linspace(-0.1, 0.1, 1000)
    flux = models.transit_model(t, period=3.5, t0=0.0, rp_rs=0.1, a_rs=8.0, inc=90.0)
    depth = 1.0 - flux.min()
    assert depth > 0.1**2
    assert depth < 2 * 0.1**2


def test_batman_is_flat_far_from_transit():
    t = np.linspace(1.0, 1.5, 200)  # nowhere near t0=0 with period 3.5
    flux = models.transit_model(t, period=3.5, t0=0.0, rp_rs=0.1, a_rs=8.0)
    np.testing.assert_allclose(flux, 1.0, atol=1e-9)


def test_uniform_limb_darkening_gives_exactly_the_geometric_depth():
    t = np.linspace(-0.01, 0.01, 101)
    flux = models.transit_model(
        t, period=3.5, t0=0.0, rp_rs=0.1, a_rs=8.0, u=(), limb_dark="uniform"
    )
    assert 1.0 - flux.min() == pytest.approx(0.1**2, rel=1e-3)


def test_a_rs_estimate_reproduces_the_duration_it_came_from():
    """Round trip: a/Rs -> duration -> a/Rs, for a central circular transit."""
    a_rs = models.a_rs_from_duration(period=3.5, duration=0.13, rp_rs=0.1)
    duration_back = (1 + 0.1) * 3.5 / (np.pi * a_rs)
    assert duration_back == pytest.approx(0.13)


def test_a_rs_from_duration_rejects_nonsense():
    with pytest.raises(ValueError):
        models.a_rs_from_duration(period=3.5, duration=0.0)
