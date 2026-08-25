"""Period search: finding a repeating dip without knowing its period in advance.

Two methods, one result type, so you can compare them on the same curve.

**BLS** (Box Least Squares) slides a *box* — a rectangular dip — across every
trial period and reports which fits best. It is fast, it is what the Kepler
pipeline used, and it is the right first tool.

**TLS** (Transit Least Squares) does the same search with a *physically shaped*
template: a limb-darkened transit with curved ingress and egress. Because the
template matches reality more closely, it recovers small planets that BLS misses
— Hippke & Heller (2019) report roughly a 10% gain in detection efficiency for
small planets, and a sharper peak, which means a more precise period.

The cost is speed: TLS is markedly slower than BLS. Search with BLS while you are
exploring; confirm with TLS when a candidate matters.

Detection statistics differ between the two and are **not** interchangeable. BLS
reports a power in arbitrary units. TLS reports SDE (Signal Detection Efficiency),
the peak height in units of the spectrum's own standard deviation; SDE >~ 7-9 is
the usual threshold for taking a candidate seriously. Compare like with like.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

import numpy as np
from lightkurve import LightCurve

__all__ = ["PeriodSearch", "DEFAULT_THREADS", "bls_search", "tls_search"]


def _default_threads() -> int:
    """A thread count that leaves the machine usable.

    TLS's own default is *every* core, which on a laptop pins all of them, spins
    the fans, and makes the browser stutter — for a search that is rarely urgent.
    We instead leave at least two cores free and cap at four, which recovers most
    of the speedup without the heat. Raise it deliberately via ``use_threads=`` if
    you are running a long sweep and want the machine busy.
    """
    cores = os.cpu_count() or 1
    return max(1, min(4, cores - 2))


#: Threads used by `tls_search` unless you override it. See `_default_threads`.
DEFAULT_THREADS = _default_threads()


@dataclass
class PeriodSearch:
    """The outcome of a period search, normalized across methods."""

    method: str
    period: float
    """Best-fit period, days."""
    epoch: float
    """Mid-transit time of a reference transit, in the input time format."""
    duration: float
    """Transit duration, days."""
    depth: float
    """Fractional transit depth (0.01 means a 1% dip)."""
    power: float
    """Peak height of the detection statistic."""
    power_label: str
    """What `power` actually is — 'SDE' or 'BLS power'. They are not comparable."""
    periods: np.ndarray = field(repr=False)
    """Trial periods searched."""
    spectrum: np.ndarray = field(repr=False)
    """Detection statistic at each trial period."""
    raw: object = field(default=None, repr=False)
    """The underlying lightkurve/TLS result, for anything not surfaced here."""

    @property
    def rp_rs(self) -> float:
        """Radius ratio implied by the depth, assuming no dilution or limb darkening.

        This is the back-of-envelope sqrt(depth). It is a *lower* bound on the true
        ratio if anything else is diluting your aperture, and limb darkening makes
        the observed central depth deeper than (Rp/Rs)**2, so treat it as a
        first estimate rather than a measurement.
        """
        return float(np.sqrt(max(self.depth, 0.0)))

    def summary(self) -> str:
        return (
            f"{self.method}: P = {self.period:.5f} d, t0 = {self.epoch:.4f}, "
            f"duration = {self.duration * 24:.2f} h, depth = {self.depth * 1e6:.0f} ppm, "
            f"Rp/Rs ~ {self.rp_rs:.4f}, {self.power_label} = {self.power:.1f}"
        )

    def compare_to(self, published: float) -> str:
        """Format the fractional disagreement against a published period."""
        err = abs(self.period - published) / published * 100
        return f"recovered {self.period:.5f} d vs published {published:.5f} d -> {err:.3f}% off"


def bls_search(
    lc: LightCurve,
    *,
    period_min: float = 1.0,
    period_max: float = 10.0,
    n_periods: int = 20_000,
    durations: tuple[float, ...] = (0.05, 0.1, 0.15, 0.2, 0.25),
) -> PeriodSearch:
    """Box Least Squares search over a linear period grid.

    ``durations`` are the trial transit lengths in days. BLS evaluates every
    (period, duration, epoch) combination, so widening this costs time roughly
    linearly.

    lightkurve may print a warning here that "`period` contains N points" for some N
    much larger than ``n_periods``. That refers to the *default* grid it builds
    before noticing you supplied your own; only ``n_periods`` points are actually
    evaluated. You can verify it with ``len(result.raw.period)``.
    """
    grid = np.linspace(period_min, period_max, n_periods)
    pg = lc.to_periodogram(method="bls", period=grid, duration=list(durations))

    # BLS depth comes back as a Quantity in the light curve's flux units; for a
    # normalized curve that is dimensionless, which is what we want.
    depth = pg.depth_at_max_power
    return PeriodSearch(
        method="BLS",
        period=float(pg.period_at_max_power.value),
        epoch=float(pg.transit_time_at_max_power.value),
        duration=float(pg.duration_at_max_power.value),
        depth=float(getattr(depth, "value", depth)),
        power=float(pg.max_power.value),
        power_label="BLS power",
        periods=np.asarray(pg.period.value, dtype=float),
        spectrum=np.asarray(pg.power.value, dtype=float),
        raw=pg,
    )


def tls_search(
    lc: LightCurve,
    *,
    period_min: float = 1.0,
    period_max: float = 10.0,
    oversampling_factor: int = 3,
    duration_grid_step: float = 1.1,
    use_threads: int = DEFAULT_THREADS,
    show_progress: bool = False,
) -> PeriodSearch:
    """Transit Least Squares search with a limb-darkened transit template.

    Unlike BLS this builds its own period grid, spaced so that neighbouring trial
    periods stay within a fraction of a transit duration of each other across the
    whole baseline — which is why you give it a range rather than a grid.

    This is the expensive call in the toolkit. Cost scales with the baseline, the
    number of cadences, and the width of ``[period_min, period_max]``, so narrow
    the period range when you can — searching 3-4 days is far cheaper than 1-10.
    Lower ``oversampling_factor`` and raise ``duration_grid_step`` to go faster at
    some cost in sensitivity.

    ``use_threads`` defaults to `DEFAULT_THREADS`, which deliberately leaves cores
    free rather than saturating the machine the way TLS does out of the box.
    """
    from transitleastsquares import transitleastsquares

    time = np.asarray(lc.time.value, dtype=float)
    flux = np.asarray(lc.flux.value, dtype=float)
    err = np.asarray(lc.flux_err.value, dtype=float)

    finite = np.isfinite(time) & np.isfinite(flux)
    # TLS rejects non-finite or non-positive uncertainties, which real curves have.
    if not np.all(np.isfinite(err[finite])) or np.any(err[finite] <= 0):
        err = None
        model = transitleastsquares(time[finite], flux[finite])
    else:
        model = transitleastsquares(time[finite], flux[finite], err[finite])

    res = model.power(
        period_min=period_min,
        period_max=period_max,
        oversampling_factor=oversampling_factor,
        duration_grid_step=duration_grid_step,
        use_threads=max(1, int(use_threads)),
        show_progress_bar=show_progress,
    )

    # TLS reports `depth` as the flux level at the transit floor (e.g. 0.99 for a
    # 1% dip), not as the dip size. Convert so it means the same thing as BLS's.
    depth = 1.0 - float(res.depth)

    return PeriodSearch(
        method="TLS",
        period=float(res.period),
        epoch=float(res.T0),
        duration=float(res.duration),
        depth=depth,
        power=float(res.SDE),
        power_label="SDE",
        periods=np.asarray(res.periods, dtype=float),
        spectrum=np.asarray(res.power, dtype=float),
        raw=res,
    )
