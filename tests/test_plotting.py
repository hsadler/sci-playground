"""Plot helpers: check the data that lands on the axes, not how it looks."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from skyplay import plotting

from .conftest import TRUE_EPOCH, TRUE_PERIOD


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


def test_binned_line_spans_the_full_orbit_by_default(times, planet_flux):
    ax = plotting.plot_folded(times, planet_flux, TRUE_PERIOD, TRUE_EPOCH, bins=100)
    x = ax.lines[0].get_xdata()
    assert x.min() < -0.4 and x.max() > 0.4


def test_zoomed_fold_bins_across_the_window_not_the_whole_orbit(times, planet_flux):
    """Regression: binning over the orbit left ~12 bins across a zoomed transit,
    rendering curved ingress as a few straight segments."""
    window, bins = 0.05, 60
    ax = plotting.plot_folded(
        times, planet_flux, TRUE_PERIOD, TRUE_EPOCH, phase_window=window, bins=bins
    )
    x = ax.lines[0].get_xdata()
    assert len(x) == bins
    assert x.min() >= -window and x.max() <= window

    # The real fix is resolution: every bin must be `2 * window / bins` wide, so the
    # transit is sampled finely. Binning over the orbit instead would have made each
    # bin `1 / bins` wide — 30x coarser here — leaving a handful of bins in view.
    assert np.diff(x) == pytest.approx(2 * window / bins)
    assert np.isfinite(ax.lines[0].get_ydata()).sum() > bins * 0.1


def test_zoomed_fold_sets_limits_to_the_window(times, planet_flux):
    ax = plotting.plot_folded(times, planet_flux, TRUE_PERIOD, TRUE_EPOCH, phase_window=0.05)
    assert ax.get_xlim() == pytest.approx((-0.05, 0.05))


def test_folded_plot_is_labelled(times, planet_flux):
    ax = plotting.plot_folded(times, planet_flux, TRUE_PERIOD, TRUE_EPOCH)
    assert ax.get_xlabel() and ax.get_ylabel()
    # A legend keeps identity off color alone, which the palette's contrast
    # warning for low-contrast slots requires.
    assert ax.get_legend() is not None


def test_spectrum_marks_the_peak(planet_lc):
    from skyplay import periods

    found = periods.bls_search(planet_lc, period_min=2, period_max=6, n_periods=1500)
    ax = plotting.plot_spectrum(found)
    assert found.power_label in ax.get_ylabel()
    texts = [t.get_text() for t in ax.texts]
    assert any(f"{found.period:.5f}" in t for t in texts)


def test_compare_spectra_uses_one_panel_per_method(planet_lc):
    """Different statistics must never share an axis — small multiples, not twins."""
    from skyplay import periods

    a = periods.bls_search(planet_lc, period_min=2, period_max=6, n_periods=1500)
    b = periods.bls_search(planet_lc, period_min=2, period_max=6, n_periods=1200)
    fig = plotting.compare_spectra([a, b])
    assert len(fig.axes) == 2
    # No twinned axes sharing a position.
    positions = [tuple(ax.get_position().bounds) for ax in fig.axes]
    assert len(set(positions)) == 2


def test_compare_spectra_rejects_more_series_than_validated_colors(planet_lc):
    from skyplay import periods

    found = periods.bls_search(planet_lc, period_min=2, period_max=6, n_periods=800)
    with pytest.raises(ValueError, match="at most"):
        plotting.compare_spectra([found] * (len(plotting.SERIES) + 1))


def test_compare_spectra_needs_a_result():
    with pytest.raises(ValueError):
        plotting.compare_spectra([])


def test_series_colors_are_distinct_hex():
    assert len(set(plotting.SERIES)) == len(plotting.SERIES)
    assert all(c.startswith("#") and len(c) == 7 for c in plotting.SERIES)
