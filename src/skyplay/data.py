"""Finding and loading real mission data from the MAST archive.

Everything here hits the network on a cache miss. The functions are thin on
purpose — the goal is to remove the repeated download/stitch/clean incantation
from the notebooks, not to hide what lightkurve is doing.

A note on time scales, which is the single most common source of silent errors in
this field: Kepler timestamps are BKJD (BJD - 2454833) and TESS timestamps are
BTJD (BJD - 2457000), both on the TDB scale. If you compare an epoch from a paper
against one you measured and get an answer that is wrong by ~2.4 million, this is
why. Let astropy's `Time` do the conversions; never subtract raw floats from
different missions.
"""

from __future__ import annotations

from dataclasses import dataclass

import lightkurve as lk

from .cache import cached

__all__ = ["Target", "TARGETS", "search", "load_stitched", "load_tpf"]


@dataclass(frozen=True)
class Target:
    """A star we care about, with published values to check our answers against.

    Published values are the whole point of the learning path: a pipeline that
    "finds a planet" is worthless until it reproduces a number someone else
    measured independently.
    """

    name: str
    """The archive-resolvable identifier, e.g. 'KIC 6922244'."""
    common_name: str
    """What humans call it, e.g. 'Kepler-8'."""
    mission: str = "Kepler"
    period: float | None = None
    """Published orbital period, days."""
    rp_rs: float | None = None
    """Published planet-to-star radius ratio."""
    epoch: float | None = None
    """Published transit epoch, in the mission's native time format (BKJD/BTJD)."""
    note: str = ""

    def __str__(self) -> str:
        return f"{self.common_name} ({self.name})"


#: Targets used across the notebooks. Published values are cited in the notes.
TARGETS: dict[str, Target] = {
    "kepler-8": Target(
        name="KIC 6922244",
        common_name="Kepler-8",
        period=3.52254,
        rp_rs=0.094,
        epoch=131.6930,
        note="Hot Jupiter. Discovery: Jenkins et al. 2010, ApJ 724, 1108.",
    ),
    "boyajians-star": Target(
        name="KIC 8462852",
        common_name="Boyajian's Star",
        note=(
            "Famous for deep, aperiodic, asymmetric dips that are NOT transits. "
            "A useful reminder that 'a dip' and 'a planet' are different claims."
        ),
    ),
}


def resolve(target: str | Target) -> Target:
    """Look up a `Target` by key, or pass one through unchanged.

    Unknown strings are treated as raw archive identifiers, so you can hand this
    any KIC/TIC/EPIC name without registering it first.
    """
    if isinstance(target, Target):
        return target
    key = target.strip().lower()
    if key in TARGETS:
        return TARGETS[key]
    return Target(name=target, common_name=target)


def search(
    target: str | Target,
    *,
    author: str = "Kepler",
    cadence: str = "long",
    quarter: int | list[int] | None = None,
) -> lk.SearchResult:
    """Search MAST for light-curve products. Returns lightkurve's `SearchResult`.

    Prefer selecting data by ``quarter=`` over slicing the result by index.
    Index order happens to match quarter order today, but it is a property of the
    archive's response, not a guarantee.
    """
    return lk.search_lightcurve(
        resolve(target).name, author=author, cadence=cadence, quarter=quarter
    )


def load_stitched(
    target: str | Target,
    *,
    quarters: tuple[int, ...] = (1, 2, 3, 4),
    author: str = "Kepler",
    cadence: str = "long",
    quality_bitmask: str = "default",
    use_cache: bool = True,
    refresh: bool = False,
) -> lk.LightCurve:
    """Download several quarters, normalize each, concatenate, and drop NaNs.

    Stitching normalizes each quarter to its own median before concatenating.
    That is necessary because the star lands on a different detector each quarter
    with a different sensitivity, so raw electron counts are not comparable across
    quarter boundaries — but it also means any real astrophysical variability on
    timescales longer than a quarter is removed along with the instrumental step.
    Do not go looking for long-period signals in a stitched curve.

    ``quality_bitmask='default'`` drops cadences the mission pipeline flagged as
    bad (thruster firings, cosmic rays, and similar).
    """
    tgt = resolve(target)

    def build() -> lk.LightCurve:
        result = search(tgt, author=author, cadence=cadence, quarter=list(quarters))
        if len(result) == 0:
            raise LookupError(
                f"No {author} {cadence}-cadence data found for {tgt} in quarters {quarters}."
            )
        collection = result.download_all(quality_bitmask=quality_bitmask)
        return collection.stitch().remove_nans()

    if not use_cache:
        return build()

    key = (
        f"{tgt.name.replace(' ', '_')}-{author}-{cadence}"
        f"-q{'_'.join(map(str, quarters))}-{quality_bitmask}-stitched"
    )
    return cached(key, build, refresh=refresh)


def load_tpf(
    target: str | Target,
    *,
    quarter: int = 4,
    author: str = "Kepler",
    cadence: str = "long",
) -> lk.KeplerTargetPixelFile:
    """Download a single Target Pixel File — the actual images behind the flux.

    Not cached here: lightkurve already caches the raw FITS download, and a TPF is
    a pixel cube rather than a table, so the Parquet cache does not apply.
    """
    result = lk.search_targetpixelfile(
        resolve(target).name, author=author, cadence=cadence, quarter=quarter
    )
    if len(result) == 0:
        raise LookupError(f"No target pixel file found for {resolve(target)} in Q{quarter}.")
    return result.download()
