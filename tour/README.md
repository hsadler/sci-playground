# The Grand Tour

[← repo overview](../README.md)

The missing middle of goal 1. The [primer](../primer/README.md) gives vocabulary and the
[course](../course/README.md) goes deep on one method (transits) — but between them there was
no place to just *look around*: to see the objects themselves, the data each kind produces,
and where the live scientific action is for each. That is what this section is.

Every stop is a notebook built to one template:

1. **See it** — real images, pulled live from public archives, never stock photos.
2. **The data** — what measurements this object class actually produces (images, light
   curves, spectra, catalogs, timing...), with a real example of each.
3. **The frontier** — what is genuinely unknown about these objects right now.
4. **What's next** — which instrument or survey is about to move it, and when.
5. **Where a hobbyist fits** — the honest version, linking to [IDEAS.md](../IDEAS.md) when a
   stop connects to goal 2.

Like the primer and course, everything is computed from real data and checked — but a stop is
a *tour*, not a method deep-dive. When a stop earns a deep-dive, that's a course extension or
an exploration.

## Itinerary

Ordered roughly near → far. `built` stops run end-to-end; `planned` stops list the frontier
one-liner they will be built around — ask for the next one you want.

| # | stop | status | the frontier, in one line |
|---|---|---|---|
| t01 | [One sky, many eyes](t01_one_sky_many_eyes.ipynb) | **built** | one object, radio → gamma rays: every wavelength is a different physics instrument |
| t02 | [The solar neighborhood](t02_the_solar_neighborhood.ipynb) | **built** | Gaia's billion-star census; DR4 (2 Dec 2026) adds ~20,000 astrometric exoplanet candidates |
| t03 | The solar system's small bodies | planned | Rubin found 11,000 new asteroids *during commissioning*; a third interstellar visitor passed in 2025 |
| t04 | Variable and exploding stars | planned | ZTF/ASAS-SN stream alerts nightly today; Rubin's LSST (started June 2026) scales that to ~10 million alerts a night |
| t05 | Stellar nurseries | planned | JWST sees through the dust to stars in the act of forming |
| t06 | Exoplanets beyond transits | planned | the course covers detection; the frontier is atmospheres (JWST) and the coming wave: PLATO (launch ~Dec 2026) and Roman (~2027) |
| t07 | The Milky Way as a galaxy | planned | stellar streams and "galactic archaeology" — reading the Galaxy's merger history from star motions |
| t08 | Galaxies and their black holes | planned | SDSS spectra by the million, the EHT's black-hole images, and quasars as probes of the early universe |
| t09 | The violent universe | planned | gravitational waves + gamma-ray bursts + fast radio bursts — astronomy with messengers that aren't light |
| t10 | The edge | planned | JWST's "too big, too early" galaxies and the Hubble-tension argument about how fast the universe expands |

## Why this moment is a good one to take the tour

The tour lands in what is plausibly the best year for new astronomical data in a generation:
Rubin's ten-year survey of the entire southern sky **began in June 2026**; **Gaia DR4** is due
2 December 2026; **PLATO** launches around the end of 2026 and **Roman** in ~2027. Several
stops will get a "what's next" section that comes true while you're reading it.

## Data footprint

Stops cache their downloads under `../data/cache/tour/` (gitignored, `make clean-cache`
deletes it), so first runs need the network and a few minutes; re-runs are offline and fast.
