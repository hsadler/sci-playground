"""Injection and recovery. All offline: synthetic curves, no archive."""

from __future__ import annotations

import lightkurve as lk
import numpy as np
import pytest

from skyplay import injection, models
from skyplay.synthetic import KEPLER_LONG_CADENCE, fold_phase, observe
from skyplay.vetting import measure_depth

from .conftest import TRUE_EPOCH, TRUE_PERIOD

# ------------------------------------------------------------------- geometry


def test_a_rs_matches_the_solar_density_scaling():
    """a/Rs = 4.20 * P^(2/3) for a Sun-density star -- a number worth pinning."""
    assert models.a_rs_from_density(1.0) == pytest.approx(4.204, rel=1e-3)
    assert models.a_rs_from_density(8.0) == pytest.approx(4.204 * 4.0, rel=1e-3)


def test_denser_star_means_larger_a_over_rs():
    assert models.a_rs_from_density(3.5, 4.0) > models.a_rs_from_density(3.5, 1.0)


def test_hot_jupiter_duration_is_a_few_hours():
    hours = models.transit_duration(3.5, 0.094) * 24
    assert 2.5 < hours < 4.0, hours


def test_duration_grows_slowly_with_period():
    """duration ~ P^(1/3): an 8x longer period is only ~2x longer in transit."""
    ratio = models.transit_duration(8.0) / models.transit_duration(1.0)
    assert ratio == pytest.approx(2.0, rel=0.02)


def test_a_rs_round_trips_through_duration():
    a_rs = models.a_rs_from_density(3.5)
    duration = models.transit_duration(3.5, 0.1)
    assert models.a_rs_from_duration(3.5, duration, 0.1) == pytest.approx(a_rs, rel=1e-6)


# ------------------------------------------------------------------ injection


@pytest.fixture
def quiet_lc():
    """A featureless noisy curve: nothing to find unless we put it there."""
    t = np.arange(0, 120, KEPLER_LONG_CADENCE)
    flux = observe(np.ones_like(t), noise=2e-4, rng=99)
    return lk.LightCurve(time=t, flux=flux, flux_err=np.full_like(flux, 2e-4))


def test_injection_puts_a_transit_at_the_requested_depth(quiet_lc):
    injected = injection.inject_transit(quiet_lc, period=4.0, epoch=1.0, depth=1e-3)
    phase = fold_phase(injected.time.value, 4.0, 1.0)
    depth = measure_depth(phase, injected.flux.value, center=0.0, halfwidth=0.002)
    # Limb darkening deepens the centre above the geometric depth, but not by much.
    assert 1e-3 <= depth < 1.5e-3, depth


def test_injection_leaves_out_of_transit_flux_alone(quiet_lc):
    injected = injection.inject_transit(quiet_lc, period=4.0, epoch=1.0, depth=1e-3)
    phase = fold_phase(injected.time.value, 4.0, 1.0)
    away = np.abs(phase) > 0.1
    np.testing.assert_allclose(injected.flux.value[away], quiet_lc.flux.value[away], rtol=1e-12)


def test_depth_and_rp_rs_agree(quiet_lc):
    by_depth = injection.inject_transit(quiet_lc, period=4.0, epoch=1.0, depth=4e-4)
    by_radius = injection.inject_transit(quiet_lc, period=4.0, epoch=1.0, rp_rs=0.02)
    np.testing.assert_allclose(by_depth.flux.value, by_radius.flux.value, rtol=1e-9)


def test_injection_rejects_ambiguous_or_impossible_input(quiet_lc):
    with pytest.raises(ValueError, match="exactly one"):
        injection.inject_transit(quiet_lc, period=4.0, epoch=1.0, depth=1e-3, rp_rs=0.03)
    with pytest.raises(ValueError, match="exactly one"):
        injection.inject_transit(quiet_lc, period=4.0, epoch=1.0)
    with pytest.raises(ValueError, match="depth"):
        injection.inject_transit(quiet_lc, period=4.0, epoch=1.0, depth=-1e-3)


def test_injection_multiplies_rather_than_adds(quiet_lc):
    """A transit removes a *fraction* of the light, so a brighter curve loses more."""
    scaled = quiet_lc.copy()
    scaled.flux = quiet_lc.flux * 2.0
    a = injection.inject_transit(quiet_lc, period=4.0, epoch=1.0, depth=1e-2)
    b = injection.inject_transit(scaled, period=4.0, epoch=1.0, depth=1e-2)
    np.testing.assert_allclose(b.flux.value, 2.0 * a.flux.value, rtol=1e-12)


# --------------------------------------------------------------------- masking


def test_masking_removes_in_transit_cadences(planet_lc):
    masked = injection.mask_transits(planet_lc, TRUE_PERIOD, TRUE_EPOCH, 0.12)
    assert len(masked) < len(planet_lc)
    phase = fold_phase(masked.time.value, TRUE_PERIOD, TRUE_EPOCH)
    # Nothing left inside the transit window.
    assert np.min(np.abs(phase) * TRUE_PERIOD) > 0.12 / 2 * 0.99


def test_masking_removes_the_signal_a_search_would_find(planet_lc):
    from skyplay import periods

    before = periods.bls_search(planet_lc, period_min=2, period_max=6, n_periods=3000)
    assert before.period == pytest.approx(TRUE_PERIOD, rel=0.01)

    masked = injection.mask_transits(planet_lc, TRUE_PERIOD, TRUE_EPOCH, 0.12)
    after = periods.bls_search(masked, period_min=2, period_max=6, n_periods=3000)
    assert after.period != pytest.approx(TRUE_PERIOD, rel=0.01)


# -------------------------------------------------------------------- recovery


def test_is_recovered_accepts_the_true_period_and_rejects_others():
    from skyplay.periods import PeriodSearch

    def result(period):
        return PeriodSearch(
            method="x",
            period=period,
            epoch=0.0,
            duration=0.1,
            depth=1e-3,
            power=1.0,
            power_label="p",
            periods=np.array([period]),
            spectrum=np.array([1.0]),
        )

    assert injection.is_recovered(result(4.0), 4.0)
    assert injection.is_recovered(result(4.02), 4.0, tolerance=0.02)
    assert not injection.is_recovered(result(4.5), 4.0)
    # Aliases are excluded by default, because counting them inflates completeness.
    assert not injection.is_recovered(result(8.0), 4.0)
    assert injection.is_recovered(result(8.0), 4.0, allow_aliases=True)
    assert injection.is_recovered(result(2.0), 4.0, allow_aliases=True)


def test_recovery_grid_finds_deep_transits_and_misses_shallow_ones(quiet_lc):
    """The whole point: completeness must fall off toward shallow depths."""
    rmap = injection.recovery_grid(quiet_lc, periods=(4.0,), depths=(1e-6, 2e-3), n_trials=3, rng=5)
    assert rmap.fraction.shape == (2, 1)
    assert rmap.fraction[0, 0] == 0.0, "a 1 ppm transit must not be recoverable"
    assert rmap.fraction[1, 0] == 1.0, "a 2000 ppm transit must be recovered"


def test_recovery_map_summary_reports_the_grid(quiet_lc):
    rmap = injection.recovery_grid(quiet_lc, periods=(4.0,), depths=(2e-3,), n_trials=2, rng=5)
    text = rmap.summary()
    assert "2000 ppm" in text
    assert "%" in text
    assert rmap.n_trials == 2


def test_recovery_grid_is_reproducible_from_a_seed(quiet_lc):
    kwargs = dict(periods=(4.0,), depths=(3e-4,), n_trials=4)
    a = injection.recovery_grid(quiet_lc, rng=7, **kwargs)
    b = injection.recovery_grid(quiet_lc, rng=7, **kwargs)
    np.testing.assert_array_equal(a.fraction, b.fraction)


def test_recovery_grid_accepts_a_custom_pipeline(quiet_lc):
    """You must be able to characterise *your* pipeline, not only the default."""
    calls = []

    def pipeline(lc):
        calls.append(1)
        return injection.default_pipeline(lc, n_periods=1500)

    injection.recovery_grid(
        quiet_lc, periods=(4.0,), depths=(2e-3,), n_trials=2, pipeline=pipeline, rng=1
    )
    assert len(calls) == 2


# ------------------------------------------------------ depth -> planet radius


def test_depth_converts_to_a_planet_radius():
    """Kepler-8 b: 8,400 ppm on a 1.49 Rsun star. Archive says 15.9 Earth radii."""
    assert models.planet_radius_earth(8.4e-3, 1.49) == pytest.approx(15.9, rel=0.1)


def test_earth_across_the_sun_is_one_earth_radius():
    """The definitional check: 84 ppm on a 1 Rsun star must give ~1 Re."""
    assert models.planet_radius_earth(8.4e-5, 1.0) == pytest.approx(1.0, rel=0.02)


def test_the_same_depth_is_a_much_smaller_planet_on_a_smaller_star():
    """The quantitative form of 'M dwarfs are the best transit targets'."""
    on_f_star = models.planet_radius_earth(5e-4, 1.49)
    on_m_dwarf = models.planet_radius_earth(5e-4, 0.30)
    assert on_f_star == pytest.approx(3.63, rel=0.02)
    assert on_m_dwarf == pytest.approx(0.73, rel=0.02)
    # Radius scales linearly with the star, so the ratio is just the radius ratio.
    assert on_f_star / on_m_dwarf == pytest.approx(1.49 / 0.30, rel=1e-6)


def test_radius_scales_as_sqrt_depth():
    """4x the depth is 2x the radius -- the (Rp/Rs)^2 relation, inverted."""
    assert models.planet_radius_earth(4e-4, 1.0) == pytest.approx(
        2 * models.planet_radius_earth(1e-4, 1.0), rel=1e-9
    )


def test_planet_radius_rejects_impossible_input():
    with pytest.raises(ValueError, match="depth"):
        models.planet_radius_earth(-1e-4, 1.0)
    with pytest.raises(ValueError, match="stellar radius"):
        models.planet_radius_earth(1e-4, 0.0)
