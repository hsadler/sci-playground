"""Injection and recovery: measuring what your pipeline can and cannot see.

This is the step that turns a search into a result, and the one most often skipped.

The problem it solves: you run a search over 500 stars, find nothing, and have learned
**nothing** — because you cannot distinguish "there are no planets here" from "my
pipeline cannot detect the planets that are here." A null result is only a statement
about the universe once you know your own sensitivity.

The method is direct. Take a real light curve, add a synthetic transit whose parameters
you chose, run your *entire* pipeline on it, and ask whether the search recovers what you
put in. Repeat across a grid of periods and depths, and the answer is a **completeness
map**: the fraction recovered at each point in parameter space.

Two details that decide whether the answer means anything:

1. **Inject before detrending, not after.** The detrending step is part of your pipeline
   and it eats signal (see `skyplay.detrend`). Injecting into an already-flattened curve
   measures only the period search and will flatter you.
2. **Vary the epoch across trials.** A transit that lands in a data gap is missed for
   reasons that have nothing to do with its depth. Several random epochs per grid cell
   average that out. Real work uses hundreds per cell; the defaults here use a handful,
   which is enough to see the shape of the boundary but too few for a published number.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np
from lightkurve import LightCurve

from . import models
from .detrend import savgol_flatten
from .periods import PeriodSearch, bls_search
from .synthetic import fold_phase

__all__ = [
    "inject_transit",
    "mask_transits",
    "default_pipeline",
    "is_recovered",
    "RecoveryMap",
    "recovery_grid",
]


def inject_transit(
    lc: LightCurve,
    *,
    period: float,
    epoch: float,
    depth: float | None = None,
    rp_rs: float | None = None,
    duration: float | None = None,
    density_solar: float = 1.0,
) -> LightCurve:
    """Multiply a synthetic limb-darkened transit into a light curve.

    Give either ``depth`` (fractional dip, e.g. 5e-4) or ``rp_rs``. Depth is converted as
    ``rp_rs = sqrt(depth)``, so the *observed* central depth comes out slightly deeper
    than ``depth`` once limb darkening is applied — which is physically correct, and worth
    remembering when you read a recovery map: the label is the geometric depth, not the
    depth a fitter would measure.

    ``duration`` defaults to a central transit around a star of ``density_solar`` mean
    density, via `skyplay.models.transit_duration`. Multiplying (rather than adding) is
    the right operation on a normalized curve: a transit removes a *fraction* of the light.
    """
    if (depth is None) == (rp_rs is None):
        raise ValueError("give exactly one of depth= or rp_rs=")
    if rp_rs is None:
        assert depth is not None  # guaranteed by the check above; narrows the type
        if depth <= 0:
            raise ValueError(f"depth must be positive, got {depth}")
        rp_rs = float(np.sqrt(depth))

    if duration is None:
        duration = models.transit_duration(period, rp_rs, density_solar)
    a_rs = models.a_rs_from_duration(period, duration, rp_rs)

    time = np.asarray(lc.time.value, dtype=float)
    signal = models.transit_model(time, period=period, t0=epoch, rp_rs=rp_rs, a_rs=a_rs, inc=90.0)

    out = lc.copy()
    out.flux = lc.flux * signal
    if lc.flux_err is not None:
        out.flux_err = lc.flux_err * signal
    return out


def mask_transits(
    lc: LightCurve, period: float, epoch: float, duration: float, pad: float = 1.5
) -> LightCurve:
    """Drop the cadences inside a known transit. Returns a shorter light curve.

    Needed before injecting into a star that already hosts a planet: otherwise every
    search finds the *real* transit, which is deeper than anything you inject, and the
    recovery map comes out empty for reasons that have nothing to do with sensitivity.

    ``pad`` widens the removed window as a multiple of the duration, so ingress and
    egress go too.
    """
    half = pad * duration / 2.0
    phase_days = fold_phase(np.asarray(lc.time.value, dtype=float), period, epoch) * period
    return lc[np.abs(phase_days) > half]


def default_pipeline(
    lc: LightCurve,
    *,
    window_days: float = 18.8,
    period_min: float = 1.0,
    period_max: float = 10.0,
    n_periods: int = 4000,
) -> PeriodSearch:
    """Detrend then BLS-search — the pipeline notebooks 03 and the capstone use.

    Deliberately BLS rather than TLS: a recovery grid runs this hundreds of times, and
    TLS is orders of magnitude slower. Characterise with BLS, then confirm individual
    candidates with TLS.
    """
    flat, _ = savgol_flatten(lc, window_days=window_days)
    return bls_search(
        flat.remove_nans(),
        period_min=period_min,
        period_max=period_max,
        n_periods=n_periods,
    )


def is_recovered(
    found: PeriodSearch, true_period: float, tolerance: float = 0.02, allow_aliases: bool = False
) -> bool:
    """Did the search land on the injected period?

    ``tolerance`` is fractional. ``allow_aliases`` also counts a hit at half or double the
    true period — sometimes reasonable, since a real follow-up would spot the harmonic and
    correct it, but off by default because counting aliases as successes inflates your
    completeness.
    """
    targets = [true_period]
    if allow_aliases:
        targets += [true_period / 2.0, true_period * 2.0]
    return any(abs(found.period - p) / p < tolerance for p in targets)


@dataclass
class RecoveryMap:
    """Completeness over a grid of injected periods and depths."""

    periods: np.ndarray
    """Injected periods, days (grid columns)."""
    depths: np.ndarray
    """Injected geometric depths (grid rows)."""
    fraction: np.ndarray = field(repr=False)
    """Recovered fraction in [0, 1], shape ``(len(depths), len(periods))``."""
    n_trials: int = 1
    """Epochs tried per grid cell."""

    def summary(self) -> str:
        lines = [
            f"Recovery over {len(self.depths)} depths x {len(self.periods)} periods, "
            f"{self.n_trials} epochs each "
            f"({self.fraction.size * self.n_trials} searches)",
            "",
            "depth \\ period  " + "".join(f"{p:>8.2f}" for p in self.periods),
        ]
        for row, depth in zip(self.fraction, self.depths, strict=True):
            cells = "".join(f"{v * 100:>7.0f}%" for v in row)
            lines.append(f"{depth * 1e6:>9.0f} ppm  {cells}")
        lines += [
            "",
            f"overall recovered: {self.fraction.mean() * 100:.0f}%",
            "A row that drops to 0% is your detection floor at that depth. Any null",
            "result you report is only meaningful above it.",
        ]
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.summary()


def recovery_grid(
    lc: LightCurve,
    *,
    periods: tuple[float, ...] = (2.0, 4.0, 6.0, 8.0),
    depths: tuple[float, ...] = (6e-5, 1.2e-4, 2.5e-4, 5e-4),
    n_trials: int = 5,
    pipeline: Callable[[LightCurve], PeriodSearch] | None = None,
    tolerance: float = 0.02,
    allow_aliases: bool = False,
    rng: int | np.random.Generator = 0,
    progress: bool = False,
) -> RecoveryMap:
    """Inject transits across a (period, depth) grid and measure what comes back.

    **Cost.** This runs the whole pipeline ``len(periods) * len(depths) * n_trials``
    times — 80 searches at the defaults, around 12 seconds. It grows multiplicatively, so
    scale deliberately.

    The default depths bracket the detection floor for a Kepler long-cadence curve of
    Kepler-8's brightness. On a fainter or noisier target the floor moves, which is the
    entire reason to measure it rather than assume a single threshold.

    **On ``n_trials``.** Each trial is worth ``1/n_trials``, so five trials quantise your
    answer to 20% and carry real sampling error: a cell whose true completeness is 52%
    reads as 40% or 80% depending on the seed. Use the defaults to find the shape of the
    boundary, then raise ``n_trials`` before believing any individual number.

    ``lc`` should be the curve *before* detrending, and should not contain a real transit
    (see `mask_transits`). ``pipeline`` is any callable taking a `LightCurve` and
    returning a `PeriodSearch`; it defaults to `default_pipeline`.
    """
    if pipeline is None:
        pipeline = default_pipeline
    if not isinstance(rng, np.random.Generator):
        rng = np.random.default_rng(rng)

    start = float(np.nanmin(np.asarray(lc.time.value, dtype=float)))
    fraction = np.zeros((len(depths), len(periods)), dtype=float)

    for i, depth in enumerate(depths):
        for j, period in enumerate(periods):
            hits = 0
            for _ in range(n_trials):
                # A random epoch inside the first cycle covers every phase relationship
                # with the data gaps.
                epoch = start + float(rng.uniform(0, period))
                injected = inject_transit(lc, period=period, epoch=epoch, depth=depth)
                found = pipeline(injected)
                hits += is_recovered(found, period, tolerance, allow_aliases)
            fraction[i, j] = hits / n_trials
            if progress:
                print(
                    f"  depth {depth * 1e6:6.0f} ppm, period {period:5.2f} d "
                    f"-> {fraction[i, j] * 100:3.0f}%"
                )

    return RecoveryMap(
        periods=np.asarray(periods, dtype=float),
        depths=np.asarray(depths, dtype=float),
        fraction=fraction,
        n_trials=n_trials,
    )
