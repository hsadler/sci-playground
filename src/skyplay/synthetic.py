"""Synthetic light curves, for building intuition before touching real data.

Nothing here calls the network. The point is to generate a signal whose true
parameters you already know, so you can check whether a method recovers them.

`trapezoid_transit` is a cartoon: real transits have curved ingress/egress and a
rounded floor from limb darkening. Once you want the real shape, use
`skyplay.models.transit_model`, which is the actual Mandel & Agol (2002) model.
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "KEPLER_LONG_CADENCE",
    "trapezoid_transit",
    "fold_time",
    "fold_phase",
    "observe",
    "bin_curve",
]

#: Kepler's "long cadence" sampling: one measurement every 30 minutes, in days.
KEPLER_LONG_CADENCE = 0.5 / 24


def trapezoid_transit(
    t: np.ndarray,
    period: float,
    t0: float,
    duration: float,
    depth: float,
    ingress_frac: float = 0.1,
) -> np.ndarray:
    """A trapezoidal transit: flat bottom, linear ingress/egress ramps.

    Parameters
    ----------
    t
        Times, in days.
    period
        Days between transits.
    t0
        Time of a transit centre (same scale as ``t``).
    duration
        Total transit length in days, first to last contact.
    depth
        Fractional dip. For a dark, small planet this is ~(Rp/Rs)**2.
    ingress_frac
        Fraction of the duration spent on each sloped side. Small values give a
        flat-bottomed "U" (planet-like); 0.5 gives a "V" (grazing, or an
        eclipsing binary).

    Returns
    -------
    Normalized flux, 1.0 out of transit.
    """
    if not 0 < ingress_frac <= 0.5:
        raise ValueError(f"ingress_frac must be in (0, 0.5], got {ingress_frac}")
    if period <= 0:
        raise ValueError(f"period must be positive, got {period}")

    t = np.asarray(t, dtype=float)
    x = np.abs(fold_time(t, period, t0))
    half = duration / 2
    ramp = ingress_frac * duration

    flux = np.ones_like(x)
    flux[x < (half - ramp)] = 1 - depth
    edge = (x >= (half - ramp)) & (x < half)
    flux[edge] = 1 - depth * (half - x[edge]) / ramp
    return flux


def fold_time(t: np.ndarray, period: float, t0: float) -> np.ndarray:
    """Time since the nearest transit centre, in days, within [-period/2, +period/2).

    This is the operation that makes shallow transits visible: every orbit gets
    stacked on top of every other, so signal adds coherently while noise averages
    down as ~1/sqrt(N).
    """
    t = np.asarray(t, dtype=float)
    return ((t - t0 + 0.5 * period) % period) - 0.5 * period


def fold_phase(t: np.ndarray, period: float, t0: float) -> np.ndarray:
    """Orbital phase within [-0.5, +0.5), where 0 is a transit centre.

    Same as `fold_time` but normalized by the period, so phase 0.5 is exactly the
    opposite side of the orbit — where a secondary eclipse would sit.
    """
    return fold_time(t, period, t0) / period


def observe(
    flux: np.ndarray,
    noise: float = 5e-4,
    rng: np.random.Generator | int | None = None,
) -> np.ndarray:
    """Add white Gaussian noise, simulating photon-counting scatter.

    `noise` is the per-point standard deviation as a fraction of the flux, so
    5e-4 is 500 parts-per-million. Pass an int for a reproducible seed.
    """
    if not isinstance(rng, np.random.Generator):
        rng = np.random.default_rng(rng)
    flux = np.asarray(flux, dtype=float)
    return flux + rng.normal(0, noise, size=flux.shape)


def bin_curve(
    x: np.ndarray,
    y: np.ndarray,
    bins: int = 120,
    range_: tuple[float, float] | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Bin ``y`` into equal-width bins of ``x``, returning (centres, means).

    Empty bins come back as NaN so matplotlib leaves a gap rather than
    interpolating across a region where you have no data. Useful for drawing the
    binned average over a folded scatter plot.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    lo, hi = range_ if range_ is not None else (np.nanmin(x), np.nanmax(x))
    edges = np.linspace(lo, hi, bins + 1)

    # `sum`/`count` per bin, vectorized — avoids a Python loop over bins.
    idx = np.digitize(x, edges) - 1
    valid = (idx >= 0) & (idx < bins) & np.isfinite(y)
    counts = np.bincount(idx[valid], minlength=bins)
    totals = np.bincount(idx[valid], weights=y[valid], minlength=bins)

    means = np.divide(totals, counts, out=np.full(bins, np.nan, dtype=float), where=counts > 0)
    centres = 0.5 * (edges[:-1] + edges[1:])
    return centres, means
