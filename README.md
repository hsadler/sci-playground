# sci-playground

A personal playground for **learning observational astronomy by doing it** — and, eventually, taking a hobbyist's swing at a **real astronomical discovery**.

It has two intertwined goals:

1. **Learn the craft.** A hands-on course, built for a software engineer new to the field, that goes from "what is a light curve?" all the way to independently recovering a known exoplanet from raw telescope data — explaining every concept from first principles and linking out to wikis, docs, and papers.
2. **Attempt a discovery.** Astronomy is one of the few sciences where an individual can genuinely contribute: petabytes of public data already exist, much of it under-explored, with clear ways to verify a find. The long-term aim is to search that public data for something genuinely new — with rigorous validation, not wishful thinking, doing the real work.

The through-line of both is **healthy skepticism**: most "discoveries" are instrument artifacts or already-known objects, so the notebooks emphasize checking your answers as much as getting them.

Everything here is built around [Lightkurve](https://docs.lightkurve.org/), a toolkit for time-series data from space telescopes like Kepler and TESS, using public data from the [MAST archive](https://archive.stsci.edu/). Lightkurve is the entry point rather than the whole toolkit — see [The stack](#the-stack) for what else is in play and why.

## Getting started

This is a [uv](https://docs.astral.sh/uv/) project, pinned to **Python 3.13** via
`.python-version` (Python 3.14 breaks a native build in the dependency tree). uv
manages the interpreter too, so you don't need to install 3.13 yourself.

### 1. Install dependencies

```sh
make install          # uv sync --all-groups
```

### 2. Launch Jupyter

```sh
make run              # JupyterLab; `make notebook` for the classic interface
```

`make help` lists every target.

### 3. Open a notebook

Start with the learning path below and run cells top to bottom with `Shift+Enter`.

The notebooks import from `skyplay`, the project's own package (see
[The `skyplay` package](#the-skyplay-package)). `make install` installs it in editable
mode, so your edits to `src/skyplay/` are picked up on the next kernel restart with no
reinstall.

## The stack

Lightkurve is a convenience layer over the real ecosystem, and a couple of its
defaults are superseded. What this project uses, and why:

| Job | Library | Why not the obvious default |
|---|---|---|
| Arrays, stats, plots | numpy, scipy, matplotlib | — |
| Units, time scales, FITS, tables | [astropy](https://www.astropy.org/) | The hub of the ecosystem. Worth learning directly, not just through lightkurve |
| Archive queries | [astroquery](https://astroquery.readthedocs.io/) | MAST, SIMBAD, Vizier, Gaia, NASA Exoplanet Archive |
| Mission data access | [lightkurve](https://docs.lightkurve.org/) | — |
| Detrending | [wotan](https://github.com/hippke/wotan) | Its robust biweight preserves transit depth better than lightkurve's `flatten()` (Savitzky–Golay), which gets dragged toward in-transit points |
| Period search | [transitleastsquares](https://github.com/hippke/tls) | TLS fits a real limb-darkened transit shape instead of BLS's box: ~10% better sensitivity to small planets, and a much sharper peak. Notebook 05 shows the difference |
| Transit models | [batman](https://lkreidberg.github.io/batman/) | Analytic Mandel & Agol (2002) light curves, for fitting real depths |

Heavier Bayesian fitting tools (`emcee`, `dynesty`, `arviz`, `corner`) are an optional
extra, installed with `uv sync --extra fitting`.

**Scaling up.** The bottleneck in a real search is moving data, not CPU. Two options
worth knowing before you try to download a survey: [TIKE](https://timeseries.science.stsci.edu/)
is a free JupyterHub that runs *next to* the MAST archive with lightkurve preinstalled,
and Kepler/TESS are available as public datasets on AWS S3, which lightkurve can stream
rather than download.

## Learning path

New to observational astronomy? Work through these in order. Each one runs end-to-end
against live data and links out to further reading.

1. **`00_light_and_light_curves.ipynb`** — the concepts from scratch using synthetic
   data you generate yourself: flux vs. magnitude, what a light curve is, transit
   geometry (depth = (Rp/Rs)²), and why *folding* pulls a signal out of noise. No
   downloads needed.
2. **`01_finding_and_downloading_data.ipynb`** — real data: the Kepler/TESS missions,
   the MAST archive, cadence and quarters/sectors, and the `LightCurve` object.
3. **`02_from_pixels_to_light_curve.ipynb`** — where the flux number comes from: target
   pixel files, apertures, and aperture photometry.
4. **`03_detrending_and_finding_periods.ipynb`** — cleaning systematics with `flatten()`,
   and finding periods automatically with the BLS periodogram.
5. **`04_false_positives_and_noise.ipynb`** — the most important skill: deciding whether
   a dip is *really* a planet. Eclipsing binaries, the odd–even test, contamination, and
   stellar variability — plus the vetting checklist. Most candidates are impostors.
6. **`05_bls_vs_tls.ipynb`** — does the *shape* of the search template matter? Runs BLS
   and TLS over the same Kepler-8 curve and compares recovered period, peak sharpness,
   and cost. Also the best worked example of using the `skyplay` package end-to-end.
7. **`kepler8b_transit_recovery.ipynb`** — *capstone.* The full pipeline run end-to-end
   and **validated against published values**: independently recovers Kepler-8 b's
   orbital period (to ~0.005%) and planet/star radius ratio, and shows a real bug
   (low-outlier clipping eating the transit) to build the habit of checking your answers.

By the end you can both **find** a transit signal (00–04) and **interrogate** it (04) —
the two halves of a real detection.

## The `skyplay` package

Logic used by more than one notebook lives in `src/skyplay/` instead of being copy-pasted
between them. The notebooks stay narrative; the machinery is tested (`make test`) and
fixed in one place.

| Module | What's in it |
|---|---|
| `synthetic` | Trapezoidal transits, folding, noise, binning — signals with known answers |
| `data` | MAST search, download, stitch, and a `TARGETS` registry with published values to check against |
| `cache` | Parquet cache for *derived* curves, so a kernel restart doesn't mean re-stitching |
| `detrend` | wotan biweight and Savitzky–Golay, both taking windows in **days** |
| `periods` | `bls_search` and `tls_search`, returning one comparable `PeriodSearch` type |
| `vetting` | Secondary-eclipse, odd–even, dilution, and radius checks with a per-check verdict |
| `plotting` | Consistent folded-curve and spectrum plots |
| `models` | batman limb-darkened transit models |

```python
from skyplay import data, detrend, periods, plotting, vetting

plotting.use_style()
lc = data.load_stitched('kepler-8')                    # cached after the first run
flat, trend = detrend.biweight_flatten(lc, window_days=0.5)
found = periods.tls_search(flat, period_min=1, period_max=10)
print(found.summary())
print(vetting.vet(flat.time.value, flat.flux.value, found.period, found.epoch).summary())
```

Two gotchas the package exists to absorb:

- **Detrending window units.** lightkurve's `flatten(window_length=)` counts *cadences*;
  wotan's counts *days*. `901` cadences at Kepler long cadence is ~18.8 days — passing
  `901` to wotan silently asks for a 901-day window. Both wrappers here take days.
- **CPU.** TLS defaults to using *every* core, which pins a laptop and spins the fans.
  `skyplay.periods.DEFAULT_THREADS` leaves headroom instead; pass `use_threads=` to
  override deliberately. Narrowing the period range is the bigger win.

## Development

```sh
make check       # lint + tests
make test        # offline tests only
make fmt         # ruff format + autofix
make clean-cache # drop cached derived light curves
```

### Notebook outputs never show up as git changes

Running a notebook rewrites every figure as a fresh block of base64, so by default a
re-run looks like a huge diff even when you changed nothing. This repo uses
[nbstripout](https://github.com/kynan/nbstripout) as a **git filter** to make that
stop: outputs and execution counts are stripped from what git *stores*, while the file
on disk keeps its outputs so your plots stay visible in Jupyter.

It's a per-clone git config, so run it once:

```sh
make setup-git-filter
```

Concretely: `03_detrending_and_finding_periods.ipynb` is ~330 KB on disk with its
figures, and ~7 KB as far as git is concerned. Re-executing it top to bottom produces
**no diff at all**.

Two things to know:

- **`git checkout`/`git stash` will discard a notebook's outputs**, because the restore
  side of the filter is a no-op — git only has the stripped version to give back. Re-run
  the notebook to get its figures back.
- The filter is marked `required`, so git operations on notebooks fail loudly if the
  venv is missing rather than silently committing outputs. Run `make install` first.

If you ever want a specific notebook's outputs committed (e.g. to show validated
results on GitHub), add `"keep_output": true` to that notebook's top-level metadata —
nbstripout honours it. Be aware that re-running that notebook *will* then produce
diffs again, which is the tradeoff.

## Other notebooks

- **`python_lightkurve.ipynb`** — a short scratch walkthrough: download a target pixel
  file, turn it into a light curve, and flatten it.
- **`python_lightkurve_yt_example.ipynb`** — "Finding exoplanets with Python +
  Lightkurve": look at a star known to host a planet, then try spotting a transiting
  planet yourself.

## A note on "discovery"

The realistic outcome of an independent search is usually a candidate that gets
explained away — and that's a win, not a failure. A signal that survives every check is
a promising *candidate*, not a confirmed planet; confirmation needs stellar modeling,
statistical validation, and often professional follow-up. Always cross-match a find
against the [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/) and the
[Kepler Eclipsing Binary Catalog](http://keplerebs.villanova.edu/) first — chances are
it's already known. The value is in the disciplined process.
