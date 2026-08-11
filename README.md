# sci-playground

A personal playground for **learning observational astronomy by doing it** — and, eventually, taking a hobbyist's swing at a **real astronomical discovery**.

It has two intertwined goals:

1. **Learn the craft.** A hands-on course, built for a software engineer new to the field, that goes from "what is a light curve?" all the way to independently recovering a known exoplanet from raw telescope data — explaining every concept from first principles and linking out to wikis, docs, and papers.
2. **Attempt a discovery.** Astronomy is one of the few sciences where an individual can genuinely contribute: petabytes of public data already exist, much of it under-explored, with clear ways to verify a find. The long-term aim is to search that public data for something genuinely new — with rigorous validation, not wishful thinking, doing the real work.

The through-line of both is **healthy skepticism**: most "discoveries" are instrument artifacts or already-known objects, so the notebooks emphasize checking your answers as much as getting them.

Everything here is built around [Lightkurve](https://docs.lightkurve.org/), a toolkit for time-series data from space telescopes like Kepler and TESS, using public data from the [MAST archive](https://archive.stsci.edu/).

## Getting started

This is a [Poetry](https://python-poetry.org/) project. It's pinned to **Python 3.13** (Python 3.14 currently breaks a native build in the dependency tree).

### 1. Install dependencies

```sh
poetry install
```

### 2. Launch Jupyter

```sh
make run
```

This runs `jupyter notebook` and opens the notebook browser. (You can also use
`poetry run jupyter lab` if you prefer JupyterLab.)

If a notebook can't find the project's packages, make sure it's using the Poetry
environment as its kernel — either launch from `poetry shell` first, or select the
`sci-playground` kernel from within Jupyter.

### 3. Open a notebook

Start with the learning path below and run cells top to bottom with `Shift+Enter`.

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
6. **`kepler8b_transit_recovery.ipynb`** — *capstone.* The full pipeline run end-to-end
   and **validated against published values**: independently recovers Kepler-8 b's
   orbital period (to ~0.005%) and planet/star radius ratio, and shows a real bug
   (low-outlier clipping eating the transit) to build the habit of checking your answers.

By the end you can both **find** a transit signal (00–04) and **interrogate** it (04) —
the two halves of a real detection.

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
