# Explorations

[← repo overview](../README.md)

Where the actual work goes. `primer/` and `course/` are finished teaching material with
known answers; this is the opposite — open-ended searches on targets nobody has handed you.

Nothing in here is expected to be tidy, and nothing in here is expected to succeed. The
normal outcome of a search is a null result or an already-published object, and both are
worth keeping.

## What belongs here

- A search over a defined sample, with its completeness map and rejection log
- Injection–recovery characterisation for a new target or cadence
- Following up something odd in a single light curve
- Reproducing a published result on a target the course doesn't cover
- Dead ends, kept deliberately, with a note on why they died

## Suggested shape for a search

Name the notebook after the question, not the method — `m_dwarfs_sectors_40_50.ipynb`
rather than `bls_run_3.ipynb`. Then, per [`06_search_design.ipynb`](../course/06_search_design.ipynb):

1. **Write the sample criteria down first.** They are your selection function, and every
   claim you can make afterwards is bounded by them.
2. **Characterise before searching.** `skyplay.injection.recovery_grid` tells you what you
   could have found. A null result without it is not a result.
3. **Log every rejection and why.** Future-you cannot reconstruct this.
4. **Cross-match before getting attached** — NASA Exoplanet Archive, the TOI list, the
   Kepler Eclipsing Binary Catalog, SIMBAD.
5. **State conclusions in both depth and planet radius.** `models.planet_radius_earth`
   converts, and radius is the unit a human can picture.

## Reusable code goes to `skyplay`

If something here gets used twice, move it into `src/skyplay/` where it can be tested.
Notebooks are for narrative and one-offs; machinery belongs in the package.
