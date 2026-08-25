"""Removing trends without removing the transit.

A raw light curve drifts: the star rotates and has spots, the spacecraft warms and
cools, the target moves across the detector. All of that produces slow variation far
larger than a planetary transit. Detrending divides it out.

The danger is obvious once stated: a filter wide enough to ignore a transit will
also ignore slow real signals, and a filter narrow enough to track the star's
variability will happily absorb the transit itself, shrinking your depth or
erasing the signal. **Choose the window from the transit duration you expect.**
The usual rule of thumb is a window at least ~3x the transit duration.

Two implementations here:

- `savgol_flatten` — lightkurve's built-in `flatten()`, a Savitzky-Golay filter
  wrapped in iterative sigma-clipping.
- `biweight_flatten` — wotan's Tukey biweight, which down-weights outlying points
  within each local window instead of being pulled through them.

**Which preserves the transit better? Measured, not assumed.** Depth recovered for
Kepler-8 b at matched windows, in ppm against a true ~8,750:

======  ==================  ==============
window  savgol (clipped)    wotan biweight
======  ==================  ==============
18.8 d              8,731            8,729
 2.0 d              8,741            8,751
 0.5 d              8,645            8,717
0.25 d              8,555            8,131
0.13 d              8,270              354
======  ==================  ==============

They are equivalent at any sensible window, and at aggressive ones **lightkurve
wins outright** — the opposite of what "robust estimator" suggests. The reason is
that the two robustness strategies fail differently. Sigma-clipping compares points
against a trend fitted over the whole curve, so in-transit points look like outliers
and get excluded from the fit. The biweight is *local*: inside a 0.13-day window
sitting in a 0.13-day transit, in-transit points are the majority, so they define
the local centre and are never down-weighted. **Local robustness cannot help when
the feature you want to protect fills the window.**

So do not choose between these expecting one to rescue a bad window. Choose the
window — at least ~3x the transit duration — and either works. wotan earns its place
for other reasons: windows in real time rather than cadence counts (which matters
across the data gaps every real mission has), and a menu of trend models
(``rspline``, ``hspline``, ``median``, ...) validated for transit searches by
Hippke et al. (2019).

**A units trap that will bite you.** lightkurve's ``flatten(window_length=...)``
counts *cadences*; wotan's ``window_length=`` is in *days*. At Kepler's 30-minute
long cadence, lightkurve's 901 works out to 901 * 0.5/24 ~ 18.8 days — a very wide
window. Passing 901 to wotan asks for a 901-day window and silently does almost
nothing. The wrappers below take days in both cases and convert, so you only have
to think about this once.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from lightkurve import LightCurve

__all__ = [
    "cadence_days",
    "days_to_cadences",
    "savgol_flatten",
    "biweight_flatten",
    "estimate_noise",
]


def cadence_days(lc: LightCurve) -> float:
    """Median spacing between consecutive measurements, in days.

    Uses the median rather than the mean so data gaps (which are everywhere in
    real mission data) do not inflate the answer.
    """
    return float(np.nanmedian(np.diff(np.asarray(lc.time.value, dtype=float))))


def days_to_cadences(lc: LightCurve, window_days: float) -> int:
    """Convert a window in days to an odd number of cadences, as Savitzky-Golay needs."""
    n = int(round(window_days / cadence_days(lc)))
    n = max(n, 3)
    return n if n % 2 == 1 else n + 1


def savgol_flatten(
    lc: LightCurve, window_days: float = 18.8, **kwargs: Any
) -> tuple[LightCurve, LightCurve]:
    """Savitzky-Golay detrend via lightkurve. Returns ``(flat, trend)``.

    The default matches the ``window_length=901`` used in the earlier notebooks, so
    results stay reproducible.

    **A defence worth knowing about.** A plain Savitzky-Golay filter with a window
    near the transit duration will fit the transit as though it were trend and
    divide it away — on Kepler-8 b, a 0.13-day window takes an 8,950 ppm transit
    down to ~70 ppm, i.e. destroys it. lightkurve's `flatten` avoids most of this
    because it *iteratively sigma-clips* before fitting (``niters=3, sigma=3`` by
    default), and in-transit points are outliers to the trend, so they get excluded
    from the fit that would otherwise absorb them. With clipping left on, that same
    0.13-day window only costs ~5% of the depth.

    Do not lean on that silently: it is a default, not a guarantee, and it is weaker
    for long or shallow transits where in-transit points are less outlying. Choosing
    a window well above the duration is still the actual fix. ``**kwargs`` are passed
    to `lightkurve.LightCurve.flatten`, so you can vary ``niters``/``sigma``/
    ``polyorder`` to see this for yourself — note that ``niters=0`` raises inside
    lightkurve, so use ``niters=1, sigma=1e9`` to disable clipping.
    """
    window = days_to_cadences(lc, window_days)
    return lc.flatten(window_length=window, return_trend=True, **kwargs)


def biweight_flatten(
    lc: LightCurve,
    window_days: float = 0.5,
    method: str = "biweight",
) -> tuple[LightCurve, LightCurve]:
    """Locally-robust detrend via wotan. Returns ``(flat, trend)`` as lightkurve objects.

    ``window_days`` should be at least ~3x your expected transit duration. For a
    typical hot Jupiter (duration ~3 h) the 0.5 d default is about right.

    Take that lower bound seriously here: unlike `savgol_flatten`, this has no
    sigma-clipping pre-pass to fall back on, so a window near the transit duration
    absorbs the transit almost completely (see the table in the module docstring —
    354 ppm recovered from an 8,750 ppm transit at a 0.13 d window). Its robustness
    is computed inside the window, and cannot protect a feature that fills it.

    Other useful ``method`` values: ``'rspline'`` (robust spline), ``'hspline'``,
    ``'median'``, ``'trim_mean'``. See the wotan docs for the full set.
    """
    from wotan import flatten as wotan_flatten

    time = np.asarray(lc.time.value, dtype=float)
    flux = np.asarray(lc.flux.value, dtype=float)

    flat_flux, trend_flux = wotan_flatten(
        time, flux, window_length=window_days, method=method, return_trend=True
    )

    flat = lc.copy()
    flat.flux = flat_flux * lc.flux.unit
    if lc.flux_err is not None:
        # Dividing flux by the trend divides its uncertainty by the same factor.
        with np.errstate(divide="ignore", invalid="ignore"):
            flat.flux_err = (np.asarray(lc.flux_err.value) / trend_flux) * lc.flux.unit

    trend = lc.copy()
    trend.flux = trend_flux * lc.flux.unit

    return flat.remove_nans(), trend


def estimate_noise(lc: LightCurve, robust: bool = True) -> float:
    """Per-cadence scatter, as a fraction of the flux. Use on an already-flattened curve.

    Two estimators, with **complementary blind spots** — which is the whole reason this
    function exists rather than a one-liner at each call site:

    - ``robust=True`` (default): ``1.4826 * MAD`` about the median. Insensitive to
      outliers *and* to transits, because both are a small minority of points. Assumes the
      curve is already flat, so detrend first.
    - ``robust=False``: the successive-difference estimator ``std(diff) / sqrt(2)``.
      Insensitive to slow trends, since neighbouring points share them — but **not** to
      sharp features. Transit ingress and egress are large point-to-point jumps, and
      ``std`` is not robust, so on a curve that still contains transits this reads high.

    On the stitched Kepler-8 curve the difference is not subtle: the successive-difference
    estimator returns ~520 ppm while the true per-cadence noise is ~215 ppm, because it is
    measuring the transit it is supposed to be compared against. Masking the transits
    brings it back to ~205 ppm, in line with the robust estimator's ~217 ppm.

    The lesson generalises past this function: an estimator is only "robust" against the
    specific thing it was designed to ignore.
    """
    flux = np.asarray(lc.flux.value, dtype=float)
    flux = flux[np.isfinite(flux)]
    if flux.size < 3:
        raise ValueError("need at least 3 finite points to estimate noise")

    if robust:
        return float(1.4826 * np.median(np.abs(flux - np.median(flux))))
    return float(np.std(np.diff(flux)) / np.sqrt(2))
