"""Consistent plots for light curves and period spectra.

Two conventions worth stating, because they carry most of the readability:

**Raw points are the data cloud, not a series.** Individual cadences are plotted
small and gray. The thing you are meant to read — the binned average — gets the
color. Plotting 60,000 noisy points in a saturated hue just makes a fog.

**Detection statistics from different methods never share a y-axis.** BLS power and
TLS SDE are different quantities in different units; overlaying them on twin axes
invites a comparison that is not meaningful. `compare_spectra` therefore stacks
them as small multiples, each with its own axis and its own label.

Colors come from a palette validated for colorblind separation and contrast; the
first three slots are safe for scatter and small multiples, which is why the
comparison helpers cap out at three series.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.figure import Figure

from .periods import PeriodSearch

if TYPE_CHECKING:
    from .injection import RecoveryMap
from .synthetic import bin_curve, fold_phase

__all__ = [
    "SERIES",
    "INK",
    "SEQUENTIAL",
    "use_style",
    "plot_folded",
    "plot_spectrum",
    "compare_spectra",
    "plot_recovery_map",
]

#: Categorical series colors, in fixed order. Do not cycle or reorder — slot
#: identity is what keeps the same method the same color across every figure.
SERIES: tuple[str, ...] = ("#2a78d6", "#eb6834", "#1baf7a")

#: Text and structure colors. Labels wear ink, never a series color.
INK = {
    "primary": "#0b0b0b",
    "secondary": "#52514e",
    "muted": "#8a8985",
    "grid": "#d8d7d2",
    "cloud": "#b4b3ae",
}


#: Sequential ramp for magnitude, built as one hue light->dark from `SERIES[0]`.
#: Deliberately not a rainbow: a multi-hue ramp implies category boundaries that a
#: continuous quantity does not have, and reads in the wrong order for many viewers.
SEQUENTIAL = LinearSegmentedColormap.from_list(
    "skyplay_blue", ["#f2f6fc", "#c3d8f2", "#87b0e3", "#4a89d6", "#2a78d6", "#164a88"]
)


def use_style() -> None:
    """Apply the repo's matplotlib defaults: recessive axes, no top/right spines.

    Call once near the top of a notebook.
    """
    plt.rcParams.update(
        {
            "figure.dpi": 110,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "grid.color": INK["grid"],
            "grid.linewidth": 0.6,
            "grid.alpha": 0.7,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.edgecolor": INK["grid"],
            "axes.labelcolor": INK["secondary"],
            "axes.titlecolor": INK["primary"],
            "axes.titlesize": 11,
            "axes.titlelocation": "left",
            "axes.titlepad": 10,
            "text.color": INK["primary"],
            "xtick.color": INK["secondary"],
            "ytick.color": INK["secondary"],
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.frameon": False,
            "legend.fontsize": 9,
            "lines.linewidth": 2.0,
            "figure.constrained_layout.use": True,
        }
    )


def plot_folded(
    time: np.ndarray,
    flux: np.ndarray,
    period: float,
    epoch: float,
    *,
    bins: int = 120,
    phase_window: float | None = None,
    color: str = SERIES[0],
    label: str = "binned average",
    ax: Axes | None = None,
    title: str | None = None,
) -> Axes:
    """Phase-fold and plot: gray cadences behind a binned average.

    ``phase_window`` zooms to +/- that phase around the transit; leave it None to
    show the full orbit, which is what you want when checking for a secondary
    eclipse at phase 0.5.

    Note that ``bins`` always spans the *plotted* range, not the whole orbit. If it
    spanned the orbit, zooming in would leave only a handful of bins across the
    transit and the binned line would render the curved ingress as a few straight
    segments — a misleading picture of the very thing you zoomed in to see.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 4))

    phase = fold_phase(np.asarray(time, dtype=float), period, epoch)
    flux = np.asarray(flux, dtype=float)

    ax.scatter(phase, flux, s=2, color=INK["cloud"], alpha=0.5, linewidths=0, rasterized=True)

    span = 0.5 if phase_window is None else phase_window
    centres, means = bin_curve(phase, flux, bins=bins, range_=(-span, span))
    ax.plot(centres, means, color=color, lw=2, label=label, zorder=3)

    if phase_window is not None:
        ax.set_xlim(-phase_window, phase_window)
        finite = means[np.isfinite(means)]
        if finite.size:
            pad = 0.15 * max(np.ptp(finite), 1e-6)
            ax.set_ylim(finite.min() - pad, finite.max() + pad)

    ax.axvline(0.0, color=INK["muted"], lw=0.8, ls=":", zorder=1)
    ax.set_xlabel("Orbital phase")
    ax.set_ylabel("Normalized flux")
    ax.set_title(title or f"Folded at P = {period:.5f} d")
    ax.legend(loc="lower right")
    return ax


def plot_spectrum(
    result: PeriodSearch,
    *,
    color: str = SERIES[0],
    ax: Axes | None = None,
    mark_harmonics: bool = True,
) -> Axes:
    """Plot a period spectrum with the peak marked.

    ``mark_harmonics`` annotates half and double the best period. Those aliases are
    where the classic failure lives: an eclipsing binary found at half its true
    period puts a strong peak at P/2, so a peak at 2x your answer that looks
    similar is a reason to run the odd-even test, not a curiosity.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(9, 3.2))

    ax.plot(result.periods, result.spectrum, color=color, lw=1.2)
    ax.axvline(result.period, color=INK["muted"], lw=0.8, ls=":")
    ax.annotate(
        f"{result.period:.5f} d",
        xy=(result.period, result.power),
        xytext=(6, -2),
        textcoords="offset points",
        color=INK["primary"],
        fontsize=9,
        fontweight="bold",
    )

    if mark_harmonics:
        lo, hi = result.periods.min(), result.periods.max()
        for factor, name in ((0.5, "P/2"), (2.0, "2P")):
            alias = result.period * factor
            if lo <= alias <= hi:
                ax.axvline(alias, color=INK["muted"], lw=0.8, ls="--", alpha=0.6)
                ax.annotate(
                    name,
                    xy=(alias, ax.get_ylim()[1]),
                    xytext=(3, -12),
                    textcoords="offset points",
                    color=INK["secondary"],
                    fontsize=8,
                )

    ax.set_xlabel("Trial period (days)")
    ax.set_ylabel(result.power_label)
    ax.set_title(f"{result.method} period spectrum")
    return ax


def compare_spectra(results: list[PeriodSearch], *, published: float | None = None) -> Figure:
    """Stack period spectra as small multiples, one panel per method.

    Deliberately *not* a twin-axis overlay: the panels measure different
    statistics, so they get different axes. What is comparable across panels is
    the *location* and *sharpness* of the peak, and a shared x-axis makes exactly
    that comparison easy while keeping the y-scales honest.
    """
    if not results:
        raise ValueError("compare_spectra needs at least one result")
    if len(results) > len(SERIES):
        raise ValueError(
            f"compare_spectra supports at most {len(SERIES)} methods; "
            "the validated scatter-safe palette has three slots."
        )

    fig, axes = plt.subplots(
        len(results), 1, figsize=(9, 2.9 * len(results)), sharex=True, squeeze=False
    )
    # strict=False on purpose: SERIES has more slots than we may have results.
    for ax, result, color in zip(axes[:, 0], results, SERIES, strict=False):
        plot_spectrum(result, color=color, ax=ax)
        if published is not None:
            ax.axvline(published, color=INK["primary"], lw=1.2, ls="-", alpha=0.5, zorder=0)

    if published is not None:
        axes[0, 0].annotate(
            f"published: {published:.5f} d",
            xy=(published, axes[0, 0].get_ylim()[1]),
            xytext=(6, -26),
            textcoords="offset points",
            color=INK["secondary"],
            fontsize=8,
        )
    for ax in axes[:-1, 0]:
        ax.set_xlabel("")
    return fig


def plot_recovery_map(
    rmap: RecoveryMap, *, ax: Axes | None = None, title: str | None = None
) -> Axes:
    """Heatmap of a `skyplay.injection.RecoveryMap`.

    Every cell is labelled with its percentage as well as shaded. That is deliberate: a
    colour scale alone makes readers estimate values from a legend, the shading is
    unreadable for anyone with reduced colour vision, and the exact numbers are the point
    here — you are reading off a detection floor, not admiring a gradient.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(1.4 * len(rmap.periods) + 3, 0.8 * len(rmap.depths) + 2.4))

    ax.imshow(
        rmap.fraction,
        cmap=SEQUENTIAL,
        vmin=0.0,
        vmax=1.0,
        origin="lower",
        aspect="auto",
    )

    ax.set_xticks(range(len(rmap.periods)), [f"{p:g}" for p in rmap.periods])
    ax.set_yticks(range(len(rmap.depths)), [f"{d * 1e6:.0f}" for d in rmap.depths])
    ax.set_xlabel("Injected period (days)")
    ax.set_ylabel("Injected depth (ppm)")
    ax.set_title(title or f"Recovery fraction ({rmap.n_trials} epochs per cell)")

    for i in range(rmap.fraction.shape[0]):
        for j in range(rmap.fraction.shape[1]):
            value = rmap.fraction[i, j]
            # Ink flips to light only where the fill is dark enough to need it.
            colour = "#ffffff" if value > 0.55 else INK["primary"]
            ax.text(
                j,
                i,
                f"{value * 100:.0f}%",
                ha="center",
                va="center",
                color=colour,
                fontsize=9,
                fontweight="bold",
            )

    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    return ax
