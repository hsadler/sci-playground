# sci-playground
A place to experiment with scientific computing.

## Getting started

This repo is a [Poetry](https://python-poetry.org/) project (Python 3.12+) built around
[Lightkurve](https://docs.lightkurve.org/), a toolkit for working with time-series
data from space telescopes like Kepler and TESS.

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

If the notebook can't find the project's packages, make sure it's using the Poetry
environment as its kernel — either launch from `poetry shell` first, or select the
`sci-playground` kernel from within Jupyter.

### 3. Open a notebook

Run cells top to bottom with `Shift+Enter`.

## Learning path

If you're new to observational astronomy and how code turns telescope data into a
planet detection, work through these in order. Each one runs end-to-end and links out
to wikis, docs, and papers for going deeper.

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
5. **`kepler8b_transit_recovery.ipynb`** — *capstone.* The full pipeline run end-to-end
   and **validated against published values**: independently recovers Kepler-8 b's
   orbital period (to ~0.005%) and planet/star radius ratio, and shows a real bug
   (low-outlier clipping eating the transit) to build the habit of checking your answers.

## Other notebooks

- **`python_lightkurve.ipynb`** — a short scratch walkthrough: download a target pixel
  file, turn it into a light curve, and flatten it.
- **`python_lightkurve_yt_example.ipynb`** — "Finding exoplanets with Python +
  Lightkurve": look at a star known to host a planet, then try spotting a transiting
  planet yourself.
