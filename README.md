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

If astronomy itself is new to you, start with [`p1_whats_out_there.ipynb`](primer/p1_whats_out_there.ipynb).
Otherwise start at [`00_light_and_light_curves.ipynb`](course/00_light_and_light_curves.ipynb) and run cells top to bottom with
`Shift+Enter`.

The notebooks import from `skyplay`, the project's own package (see
[The `skyplay` package](#the-skyplay-package)). `make install` installs it in editable
mode, so your edits to `src/skyplay/` are picked up on the next kernel restart with no
reinstall.

## Layout

```
primer/         astronomy from zero - what's out there, and how it's observed
course/         the transit-hunting path, 00 through 06 plus the capstone
explorations/   open-ended searches: your own targets, no answer key
IDEAS.md        candidate projects, with the research already attached
src/skyplay/    the package the notebooks call
tests/          93 tests, all offline
```

The split is by **whether there is a right answer**. `primer/` and `course/` are finished
teaching material validated against published values, so if something there disagrees with
the literature it is a bug. `explorations/` is the opposite: real searches where a null
result is the expected outcome - see [explorations/README.md](explorations/README.md).

## The stack

Lightkurve is a convenience layer over the real ecosystem, and a couple of its
defaults are superseded. What this project uses, and why:

| Job | Library | Why not the obvious default |
|---|---|---|
| Arrays, stats, plots | numpy, scipy, matplotlib | — |
| Units, time scales, FITS, tables | [astropy](https://www.astropy.org/) | The hub of the ecosystem. Worth learning directly, not just through lightkurve |
| Archive queries | [astroquery](https://astroquery.readthedocs.io/) | MAST, SIMBAD, Vizier, Gaia, NASA Exoplanet Archive |
| Mission data access | [lightkurve](https://docs.lightkurve.org/) | — |
| Detrending | [wotan](https://github.com/hippke/wotan) | Windows in real time rather than cadence counts, which matters across the data gaps every mission has, plus a menu of trend models validated for transit searches. *Not* because it protects transits better than lightkurve's `flatten()` — measured, it doesn't; see notebook 03 §4 |
| Period search | [transitleastsquares](https://github.com/hippke/tls) | TLS fits a real limb-darkened transit shape instead of BLS's box: ~10% better sensitivity to small planets, and a much sharper peak. Notebook 05 shows the difference |
| Transit models | [batman](https://lkreidberg.github.io/batman/) | Analytic Mandel & Agol (2002) light curves, for fitting real depths |

Heavier Bayesian fitting tools (`emcee`, `dynesty`, `arviz`, `corner`) are an optional
extra, installed with `uv sync --extra fitting`.

**Scaling up.** The bottleneck in a real search is moving data, not CPU. Two options
worth knowing before you try to download a survey: [TIKE](https://timeseries.science.stsci.edu/)
is a free JupyterHub that runs *next to* the MAST archive with lightkurve preinstalled,
and Kepler/TESS are available as public datasets on AWS S3, which lightkurve can stream
rather than download.

## Primer — start here if you're new to astronomy

Four short notebooks in [`primer/`](primer/README.md) so the course doesn't assume
vocabulary you haven't met. Every claim is computed or plotted from real data.

1. [`p1_whats_out_there.ipynb`](primer/p1_whats_out_there.ipynb) — the inventory of the universe, by scale, and why distance *is* time.
2. [`p2_stars.ipynb`](primer/p2_stars.ipynb) — the reference object for everything else, with an HR diagram built from 8,000 Gaia stars.
3. [`p3_how_we_observe.ipynb`](primer/p3_how_we_observe.ipynb) — the spectrum, telescopes, and where photometric noise comes from.
4. [`p4_the_data.ipynb`](primer/p4_the_data.ipynb) — FITS, the four shapes data comes in, and the time conventions that cause silent errors.

## Course

Eight notebooks in [`course/`](course/README.md), in order. Half of it is about finding a
signal and half about doubting it, because most transit-like signals are not planets.

1. [`00_light_and_light_curves.ipynb`](course/00_light_and_light_curves.ipynb) — the concepts from scratch in pure numpy, no downloads.
2. [`01_finding_and_downloading_data.ipynb`](course/01_finding_and_downloading_data.ipynb) — real data: the missions, the MAST archive, and the `LightCurve` object.
3. [`02_from_pixels_to_light_curve.ipynb`](course/02_from_pixels_to_light_curve.ipynb) — where the flux number comes from: pixels, apertures, photometry.
4. [`03_detrending_and_finding_periods.ipynb`](course/03_detrending_and_finding_periods.ipynb) — removing trends without removing the transit, then BLS.
5. [`04_false_positives_and_noise.ipynb`](course/04_false_positives_and_noise.ipynb) — **the most important one**: deciding whether a dip is really a planet.
6. [`05_bls_vs_tls.ipynb`](course/05_bls_vs_tls.ipynb) — does the shape of the search template matter?
7. [`kepler8b_transit_recovery.ipynb`](course/kepler8b_transit_recovery.ipynb) — **capstone**: the whole pipeline, validated against published values.
8. [`06_search_design.ipynb`](course/06_search_design.ipynb) — running a search where nobody knows the answer, and measuring what you *can't* see.

Per-notebook runtimes, which ones need the network, and how the arc fits together are in
[`course/README.md`](course/README.md).

Notebooks 00 and 01 deliberately keep their hand-written and raw-`lightkurve` versions,
since building the primitive yourself is the lesson there; each then proves `skyplay`
reproduces it exactly, so nothing is taken on faith.

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
| `injection` | Inject synthetic transits, mask real ones, and build a completeness map |
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

Concretely: [`03_detrending_and_finding_periods.ipynb`](course/03_detrending_and_finding_periods.ipynb) is ~330 KB on disk with its
figures and ~15 KB as far as git is concerned. Re-executing it top to bottom leaves
`git diff` **empty** and stages nothing — outputs can't be committed even by accident.

What it does *not* do is keep `git status` quiet. Running a notebook changes its size on
disk, so the size cached in git's index no longer matches; git re-filters the file, finds
the content identical, but leaves the stale entry in place and keeps listing it. The file
shows as modified while `git diff` is empty and `git add` stages nothing. It's cosmetic,
it doesn't clear on its own, and `make nb-refresh` silences it.

Three things to know:

- **`git checkout`/`git stash` will discard a notebook's outputs**, because the restore
  side of the filter is a no-op — git only has the stripped version to give back. Re-run
  the notebook to get its figures back.
- The filter is marked `required`, so git operations on notebooks fail loudly if the
  venv is missing rather than silently committing outputs. Run `make install` first.
- **`git status` listing a notebook with an empty `git diff` is expected**, per above.
  Confirm with `git diff --no-textconv` (also empty) and clear it with `make nb-refresh`.

If you ever want a specific notebook's outputs committed (e.g. to show validated
results on GitHub), add `"keep_output": true` to that notebook's top-level metadata —
nbstripout honours it. Be aware that re-running that notebook *will* then produce
diffs again, which is the tradeoff.

## Choosing a target for an original search

The learning path always hands you the star. Picking your own is the first genuinely open
decision, and it's where a search is won or lost — the target selection determines what
you *could* find long before any code runs.

**Prefer TESS over Kepler.** Kepler's field has been picked over for a decade by people
with better tools. TESS is still producing data, covers most of the sky, and its
full-frame images are far less exhaustively searched.

**Prefer small, cool, nearby stars.** M dwarfs (effective temperature roughly
2,500–3,700 K) are the sweet spot, for two independent reasons:

- **Depth scales as (Rp/Rs)².** The same planet around a star half the Sun's radius
  gives a transit four times deeper. Small star = detectable planet.
- **Short orbits.** Cool stars have close-in habitable zones, so interesting planets
  orbit in days rather than years — and TESS observes each sector for only ~27 days, so
  you need a period short enough to fit two or three transits inside that window.

Nearby (say within ~25 parsecs) means brighter, which means better photometry per cadence.

**Where to browse.** The [MAST Portal](https://mast.stsci.edu/portal/Mashup/Clients/Mast/Portal.html)
exposes the TESS Candidate Target List (CTL, a filtered subset of the TESS Input Catalog)
under *MAST catalogs → TESS CTL → Advanced Search* — millions of rows, filterable on
temperature, distance, and magnitude. Take the TIC id of anything promising. You can also
query the same catalogs from Python via `astroquery`, which is already a dependency here
and is usually less painful than the web UI.

**Then check whether it's already known — before you get attached.** Look the target up in
[exoMAST](https://exo.mast.stsci.edu/), the
[NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/), and the
[Kepler Eclipsing Binary Catalog](http://keplerebs.villanova.edu/). Most stars with an
obvious signal already have a paper. That is not a reason to stop — reproducing a known
result is exactly how the capstone builds trust in the pipeline — but you should know
which situation you're in from the start.

If `lightkurve`'s search returns nothing for a target that MAST clearly has, the data may
only exist as a full-frame-image cutout rather than a target pixel file; reach for
`astroquery.mast` or TESSCut in that case.

## A note on "discovery"

The realistic outcome of an independent search is usually a candidate that gets
explained away — and that's a win, not a failure. A signal that survives every check is
a promising *candidate*, not a confirmed planet; confirmation needs stellar modeling,
statistical validation, and often professional follow-up. Always cross-match a find
against the [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/) and the
[Kepler Eclipsing Binary Catalog](http://keplerebs.villanova.edu/) first — chances are
it's already known. The value is in the disciplined process.
