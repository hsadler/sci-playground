# Primer — astronomy from zero

[← repo overview](../README.md)

Four short notebooks so the [course](../course/README.md) doesn't have to assume vocabulary
you haven't met. Overview-level and light on maths, but **every claim is computed or plotted
from real data** rather than asserted — the HR diagram is 8,000 actual Gaia stars, the
spectrum is a real SDSS observation.

Skip this if you already know what an M dwarf is, what FITS is, and why photometry needs to
be done from space.

| # | Notebook | Runs in | Needs network |
|---|---|---|---|
| 1 | [`p1_whats_out_there.ipynb`](p1_whats_out_there.ipynb) | ~4 s | no |
| 2 | [`p2_stars.ipynb`](p2_stars.ipynb) | ~5 s | Gaia |
| 3 | [`p3_how_we_observe.ipynb`](p3_how_we_observe.ipynb) | ~3 s | no |
| 4 | [`p4_the_data.ipynb`](p4_the_data.ipynb) | ~13 s | MAST, Gaia, SDSS |

## What each one is for

**P1 · What's out there** — the inventory, ordered by scale: moons through the cosmic web,
plus the transients that only time-domain astronomy can catch. Two ideas carry it: distance
*is* time, and most observable things are a star, made of stars, or the corpse of one.
Closes on which technique answers which question, so you can see how narrow a window
transit photometry actually is.

**P2 · Stars** — the reference object for everything else, because every measurement in
this repo is a measurement of a star. Temperature and colour, the OBAFGKM sequence, and an
HR diagram built from Gaia showing the main sequence and a separate white-dwarf sequence.
Explains why M dwarfs are both the commonest star and the best transit target — the two
reasons are independent, and both matter for picking your own targets later.

**P3 · How we observe** — the spectrum as a set of different questions rather than one
continuum, why some telescopes *must* be in space (for photometry the reason is
scintillation, not faintness), what aperture buys, and where noise comes from. Includes the
result that transit difficulty scales as depth⁻²: an Earth needs 10,000× more photons than
a hot Jupiter.

**P4 · What the data looks like** — the gap between understanding concepts and handling
files. FITS, and the four shapes data comes in — image, light curve, spectrum, catalogue —
each with a real example. Ends on units and time systems, including the BKJD/BTJD
conventions that cause more silent errors than anything else in the field.

## After this

Start the course at [`00_light_and_light_curves.ipynb`](../course/00_light_and_light_curves.ipynb).
It reuses P1's folding idea and P3's noise budget immediately.
