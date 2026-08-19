# Course — finding a transiting planet

[← repo overview](../README.md)

Eight notebooks that go from "what is a light curve?" to running a defensible search of
your own. Work through them in order; each builds on the last.

The through-line is **healthy skepticism**. Roughly half the material is about finding a
signal and the other half about doubting it, because in real surveys most transit-like
signals are not planets. Everything here is checked against published values, so if a
number disagrees with the literature it is a bug — [report it](../explorations/README.md)
or fix it.

| # | Notebook | Runs in | Needs network | What it adds |
|---|---|---|---|---|
| 00 | [`00_light_and_light_curves.ipynb`](00_light_and_light_curves.ipynb) | ~2 s | no | Concepts from scratch, pure numpy |
| 01 | [`01_finding_and_downloading_data.ipynb`](01_finding_and_downloading_data.ipynb) | ~5 s | MAST | Real data, and the archive's vocabulary |
| 02 | [`02_from_pixels_to_light_curve.ipynb`](02_from_pixels_to_light_curve.ipynb) | ~12 s | MAST | Where the flux number comes from |
| 03 | [`03_detrending_and_finding_periods.ipynb`](03_detrending_and_finding_periods.ipynb) | ~4 s | MAST | Detrending, and BLS period search |
| 04 | [`04_false_positives_and_noise.ipynb`](04_false_positives_and_noise.ipynb) | ~3 s | MAST | **Vetting — the most important one** |
| 05 | [`05_bls_vs_tls.ipynb`](05_bls_vs_tls.ipynb) | ~67 s | MAST | Does the search template's shape matter? |
| — | [`kepler8b_transit_recovery.ipynb`](kepler8b_transit_recovery.ipynb) | ~6 s | MAST | **Capstone** — the whole pipeline, validated |
| 06 | [`06_search_design.ipynb`](06_search_design.ipynb) | ~30 s | MAST, Exoplanet Archive | Searching where no answer exists |

Times are with a warm cache. Notebook 01 downloads ~14,000 cadences on its first run and
[`skyplay.cache`](../src/skyplay/cache.py) keeps the stitched result, so everything after it
is fast. 05 is slow because TLS is genuinely expensive — that's the notebook's own point.

## The arc

**00–02 build the object.** What a light curve is, where it comes from, and how a stack of
telescope images becomes one number per timestamp. 00 needs no downloads at all and writes
its transit model by hand; it then checks that hand-written version against
`skyplay.synthetic` and asserts they agree exactly, so nothing later is taken on faith.

**03 and 05 find the signal.** Detrending without destroying the transit, then automatic
period search. Both notebooks turn up a result that contradicts the received wisdom:
lightkurve's `flatten()` quietly protects transits by sigma-clipping before it fits, and
wotan's "robust" biweight does *not* protect them better — measured, it's worse at
aggressive windows. Those sections exist because reasoning from a tool's description gave
the wrong answer and measuring gave the right one.

**04 doubts it.** Eclipsing binaries, the odd–even test, contamination, and the vetting
checklist. If you only read one, read this one: a pipeline without it will hand you a
planet every week and every one will be wrong.

**The capstone proves the pipeline.** Kepler-8 b recovered independently — period to 0.005%
and radius ratio to 0.6% of published — plus a deliberate demonstration of a bug that
silently eats transits.

**06 makes it a search.** Scoping a sample, and injection–recovery: measuring what your
pipeline *can't* see, because a search that finds nothing has told you nothing until you
know what it was capable of finding.

## After this

There is no notebook 07. Pick a target and start something in
[`explorations/`](../explorations/README.md).
