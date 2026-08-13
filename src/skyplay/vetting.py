"""Deciding whether a dip is really a planet.

This is the part that separates a discovery from an embarrassment. Most transit-like
signals are **not** planets. The common impostors:

1. **Eclipsing binaries.** Two stars orbiting each other. Tell-tales: a *secondary
   eclipse* at phase 0.5 (starlight blocked on the far side too), V-shaped rather
   than flat-bottomed dips, and depths implying Rp/Rs > ~0.2 — bigger than any
   planet can be, since objects above ~2 Jupiter radii are stars or brown dwarfs.

2. **An eclipsing binary at twice your period.** If you fold a system with unequal
   alternating eclipses at *half* its true period, the two different eclipses land
   on top of each other and average into one plausible-looking transit. The
   **odd-even test** catches it: number the transits and compare the mean depth of
   the even-numbered ones against the odd-numbered ones. A planet gives the same
   depth every time. A binary does not.

3. **Contamination / dilution.** Your aperture collects light from neighbouring
   stars too. A deep eclipse on a faint background star, diluted by a bright
   foreground star, produces a shallow planet-like depth on the wrong target. This
   is why depth alone is never enough — you must ask which pixels made the number,
   and whether the light centroid shifts during the dip.

4. **Stellar variability and systematics.** Spots, pulsations, and spacecraft
   effects all make dips. These usually fail on shape, on coherence, or on being
   present in some quarters and not others.

None of these checks *prove* a planet. They only fail candidates. A signal that
survives all of them is a candidate worth following up — not a discovery.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .synthetic import fold_phase

__all__ = [
    "measure_depth",
    "secondary_eclipse_depth",
    "odd_even_depths",
    "dilute_depth",
    "VettingReport",
    "vet",
]

#: Above this radius ratio, the companion is too big to be a planet.
MAX_PLANETARY_RP_RS = 0.2


def _baseline(phase: np.ndarray, flux: np.ndarray) -> float:
    """Median out-of-eclipse flux, sampled near quadrature (phase ~ +/-0.25).

    Quadrature is used because it is far from both the transit at phase 0 and any
    secondary eclipse at phase 0.5.
    """
    quiet = np.abs(np.abs(phase) - 0.25) < 0.05
    if not np.any(quiet):
        return float(np.nanmedian(flux))
    return float(np.nanmedian(flux[quiet]))


def measure_depth(
    phase: np.ndarray,
    flux: np.ndarray,
    center: float = 0.0,
    halfwidth: float = 0.02,
) -> float:
    """Depth of the dip in a phase window, relative to the out-of-eclipse baseline.

    Returns a fraction: 0.01 means a 1% dip. Negative means the window is *brighter*
    than baseline, which for a secondary-eclipse check just means "nothing there".
    Returns NaN if the window contains no data.
    """
    phase = np.asarray(phase, dtype=float)
    flux = np.asarray(flux, dtype=float)

    # Phase is cyclic on [-0.5, 0.5), so a window at 0.5 wraps to -0.5.
    delta = np.abs((phase - center + 0.5) % 1.0 - 0.5)
    window = (delta < halfwidth) & np.isfinite(flux)
    if not np.any(window):
        return float("nan")
    return _baseline(phase, flux) - float(np.nanmedian(flux[window]))


def secondary_eclipse_depth(
    time: np.ndarray, flux: np.ndarray, period: float, epoch: float, halfwidth: float = 0.02
) -> float:
    """Depth at phase 0.5. A clear dip there means a companion *star*, not a planet.

    Caveat: hot Jupiters do have genuine, very shallow secondary eclipses from their
    own thermal emission — tens of ppm, not the thousands a stellar companion gives.
    Scale matters more than presence.
    """
    phase = fold_phase(time, period, epoch)
    return measure_depth(phase, flux, center=0.5, halfwidth=halfwidth)


def odd_even_depths(
    time: np.ndarray,
    flux: np.ndarray,
    period: float,
    epoch: float,
    halfwidth: float = 0.02,
) -> tuple[float, float]:
    """Mean transit depth of even- vs odd-numbered transits.

    A genuine planet blocks the same amount of light every orbit, so these agree
    within the noise. An eclipsing binary folded at half its true period shows
    alternating deep and shallow eclipses, so they disagree.
    """
    time = np.asarray(time, dtype=float)
    flux = np.asarray(flux, dtype=float)

    number = np.round((time - epoch) / period).astype(int)
    phase = fold_phase(time, period, epoch)
    in_transit = (np.abs(phase) < halfwidth) & np.isfinite(flux)
    base = _baseline(phase, flux)

    def depth_for(mask: np.ndarray) -> float:
        sel = in_transit & mask
        if not np.any(sel):
            return float("nan")
        return base - float(np.nanmedian(flux[sel]))

    return depth_for(number % 2 == 0), depth_for(number % 2 == 1)


def dilute_depth(true_depth: float, neighbor_flux_ratio: float) -> float:
    """Depth you would *measure* when a neighbour's light dilutes the target's.

    ``neighbor_flux_ratio`` is the contaminating flux in the aperture relative to
    the target's. The eclipse removes light from the target only, but the depth is
    measured against the total, so the dip is diluted by 1/(1 + ratio).

    This is how a 4% stellar eclipse becomes a 1% "planet".
    """
    if neighbor_flux_ratio < 0:
        raise ValueError("neighbor_flux_ratio must be >= 0")
    return true_depth / (1.0 + neighbor_flux_ratio)


@dataclass
class VettingReport:
    """Results of the standard vetting checks, with a verdict per check."""

    period: float
    epoch: float
    transit_depth: float
    secondary_depth: float
    even_depth: float
    odd_depth: float

    @property
    def rp_rs(self) -> float:
        return float(np.sqrt(max(self.transit_depth, 0.0)))

    @property
    def secondary_ratio(self) -> float:
        """Secondary depth as a fraction of the transit depth."""
        if not np.isfinite(self.transit_depth) or self.transit_depth <= 0:
            return float("nan")
        return self.secondary_depth / self.transit_depth

    @property
    def odd_even_mismatch(self) -> float:
        """Fractional difference between odd and even depths, 0 = perfect agreement."""
        biggest = np.nanmax([self.even_depth, self.odd_depth])
        if not np.isfinite(biggest) or biggest <= 0:
            return float("nan")
        return abs(self.even_depth - self.odd_depth) / biggest

    def checks(self) -> dict[str, tuple[bool, str]]:
        """Each check as ``name -> (passed, explanation)``.

        Thresholds here are deliberately loose screening heuristics, not
        publication criteria: a real vetting effort fits models and propagates
        uncertainties instead of comparing medians to round numbers.
        """
        results: dict[str, tuple[bool, str]] = {}

        ratio = self.secondary_ratio
        results["no secondary eclipse"] = (
            bool(np.isfinite(ratio) and ratio < 0.1),
            f"secondary is {ratio * 100:.1f}% of the transit depth "
            f"({self.secondary_depth * 1e6:.0f} ppm); a stellar companion would be comparable",
        )

        mismatch = self.odd_even_mismatch
        results["odd/even depths agree"] = (
            bool(np.isfinite(mismatch) and mismatch < 0.25),
            f"{mismatch * 100:.0f}% mismatch "
            f"(even {self.even_depth * 1e6:.0f} ppm vs odd {self.odd_depth * 1e6:.0f} ppm)",
        )

        results["radius is planetary"] = (
            bool(self.rp_rs < MAX_PLANETARY_RP_RS),
            f"Rp/Rs ~ {self.rp_rs:.3f}; above {MAX_PLANETARY_RP_RS} implies a star, "
            f"not a planet (undiluted)",
        )

        return results

    @property
    def passed(self) -> bool:
        """True only if every check passes. Means 'still a candidate', not 'a planet'."""
        return all(ok for ok, _ in self.checks().values())

    def summary(self) -> str:
        lines = [
            f"Vetting at P = {self.period:.5f} d, t0 = {self.epoch:.4f}",
            f"  transit depth : {self.transit_depth * 1e6:7.0f} ppm  (Rp/Rs ~ {self.rp_rs:.4f})",
            "",
        ]
        for name, (ok, why) in self.checks().items():
            lines.append(f"  [{'PASS' if ok else 'FAIL'}] {name}: {why}")
        lines.append("")
        lines.append(
            "  => survives screening; worth following up"
            if self.passed
            else "  => fails screening; most likely not a planet"
        )
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.summary()


def vet(
    time: np.ndarray,
    flux: np.ndarray,
    period: float,
    epoch: float,
    halfwidth: float = 0.02,
) -> VettingReport:
    """Run the standard checks on a detrended curve and a candidate ephemeris.

    ``time`` and ``flux`` are plain arrays, and ``flux`` should already be
    normalized and detrended (see `skyplay.detrend`). ``halfwidth`` is the
    in-transit phase window; it should be comparable to duration/period.
    """
    phase = fold_phase(time, period, epoch)
    even, odd = odd_even_depths(time, flux, period, epoch, halfwidth=halfwidth)
    return VettingReport(
        period=period,
        epoch=epoch,
        transit_depth=measure_depth(phase, flux, center=0.0, halfwidth=halfwidth),
        secondary_depth=measure_depth(phase, flux, center=0.5, halfwidth=halfwidth),
        even_depth=even,
        odd_depth=odd,
    )
