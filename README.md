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

- **`python_lightkurve.ipynb`** — a short walkthrough: download a target pixel file for
  a star, turn it into a light curve, and flatten it. A good place to start.
- **`python_lightkurve_yt_example.ipynb`** — "Finding exoplanets with Python +
  Lightkurve": look at a star known to host a planet, then try spotting a transiting
  planet yourself by watching for periodic dips in a star's brightness.

Run cells top to bottom with `Shift+Enter`.
