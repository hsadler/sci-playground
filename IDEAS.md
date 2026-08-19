# Ideas

A running list of things worth attempting, with enough research attached that future-me can
judge them without starting over. Ideas graduate from here into
[`explorations/`](explorations/README.md).

**Status labels.** `researched` — numbers checked, literature surveyed, risks known.
`speculative` — interesting, unverified, would need a session of digging.
`parked` — looked at, not now, reason recorded.

## What makes an idea viable here

Learned the hard way, and worth re-reading before adding anything:

1. **The unit of work must be verifiable.** Ground truth, or an internal consistency check.
   Every real error caught in this repo was caught by measurement, never by reasoning harder.
2. **The bottleneck should be tedium, not insight.** Volume, plumbing, cross-catalogue
   joining, bespoke code — that is where AI assistance actually multiplies output. It does
   *not* multiply statistical judgement; it is actively hazardous there.
3. **Data must be public**, and preferably annoying to work with. Annoying is a moat.
4. **Professionals must have a reason to skip it** — unglamorous, or falling between
   specialties. "Nobody has done this" is usually false; "nobody could be bothered" is often
   true.
5. **Reproduce a known answer before chasing an unknown one.** Non-negotiable.

---

## 1. Cross-mission transit timing — `researched`

**The idea.** Measure mid-transit times for Kepler planets across both Kepler (2009–13) and
TESS (2019–), fit a linear ephemeris over the combined ~16-year baseline, and look at the
residuals. Deviations mean either a drifting ephemeris (useful) or an unseen companion
tugging on the planet (interesting).

**Why it suits this setup.** Timing is *robust* — you need consistent mid-transit times, not
absolute photometric accuracy, and systematics that would wreck a depth measurement often
cancel. Joining the two missions is pure plumbing (BKJD vs BTJD, 30-min vs 2-min vs FFI
cadence, five separate pipeline authors for one target), which repels humans and suits
agent-assisted work. And there is ground truth at every step.

**The numbers** (computed from the NASA Exoplanet Archive, `pscomppars`):

| | count |
|---|---|
| Kepler-discovered planets | 2,784 |
| …with usable depth + TESS magnitude | 2,751 |
| …TESS SNR > 10 in a single transit | 94 |
| …SNR > 5 in a single transit | 172 |
| **…SNR > 10 and P > 30 d** | **46** |
| …SNR > 10 and P > 100 d | 28 |
| …SNR > 10 and P > 200 d | 15 |

Kepler hosts are faint (median TESS mag **14.1**) and their transits shallow (median **449
ppm**), and TESS is a 10 cm lens built for bright stars — hence the brutal cut from 2,784 to
~94. **That SNR figure is a photon-limited estimate, not a measurement.** Replacing it with a
measured one is task zero.

**What is already occupied:**

- Hot Jupiters are done. [Ivshina & Winn (2022)](https://iopscience.iop.org/article/10.3847/1538-4365/ac545b)
  — 8,667 transit times, 382 systems, ~240 hot Jupiters. WASP-12 is still the only secure
  period-change detection anywhere.
- Kepler/K2 → TESS has been done once. [MNRAS 538, 2283 (2025)](https://academic.oup.com/mnras/article/538/4/2283/8093570)
  — 111 systems, timing variations newly found in 22, period precision improved 2–10x.
- There is an active pro-am network. [ExoClock](https://arxiv.org/pdf/2209.09673) has 270
  participants, 220 of them amateurs; [ExoClock IV](https://arxiv.org/pdf/2511.14407) lists
  620 updated ephemerides. Over 40% of literature ephemerides needed correcting.

**The seam.** That 111-system paper included only **six** planets beyond 30 days and states
that longer-period planets with data gaps were not fully analysed. ExoClock targets bright
short-period Ariel candidates, and its ground-based network cannot easily cover a 10-hour
transit of a 14th-magnitude star. Meanwhile the field acknowledges that
[>80% of transiting exoplanets will have >30-minute timing uncertainty by decade's end](https://iopscience.iop.org/article/10.3847/1538-3881/ab845d).

Long-period Kepler planets are the acute case, because Kepler only caught a handful of
transits each — median **7** for the P > 100 d set. An ephemeris built on seven events and
extrapolated twelve years is wide open.

**Odds.** Refining a neglected long-period ephemeris: high. Something citable (RNAAS-scale):
plausible if several are done coherently. Finding an unseen companion: moderate-low.
Detecting period decay: very low — professionals have one secure case after a decade.

**Risks.** Some of the 46 are heavily worked (Kepler-9, Kepler-51, Kepler-419). The obscure
ones are obscure because they are faint and hard. With ~7 transits per target you are doing
careful work on small numbers, where a systematic error looks exactly like a discovery.

**First step.** `skyplay` can measure depth and period but *not* a mid-transit time with an
uncertainty. That primitive is missing. Build it, validate against published times for
Kepler-8, then reproduce Kepler-9 c — the first TTV detection ever made.

---

## 2. Century-baseline photometry — `researched`

**The idea.** [DASCH DR7](https://dasch.cfa.harvard.edu/) digitised Harvard's glass plate
collection and finished in early 2024. It offers **23,574,404,199 photometric measurements of
252,458,490 sources covering the whole sky from ~1880 to 1990** — 200 TB of plate images, 16
TB of light curves, and a Python package (`daschlab`) to reach them.

Baselines an order of magnitude longer than anything born-digital, because the data
physically did not exist otherwise. Combine with ASAS-SN (2013–), ZTF (2018–) and TESS and
the window is ~140 years.

**Why it is genuinely untrodden.** The final release is recent, so systematic mining has
barely begun. And plate data is *awkward* — which is the moat.

**What it can answer.** Objects that changed state over a century. Secular period change in
pulsators. Whether something interesting now was already interesting in 1920. Historical
outbursts. Photometry is coarse (~0.1 mag), so this is for large-amplitude, long-timescale
phenomena — not precision work.

**The cautionary tale, and it is the whole risk in one story.**
[Schaefer (2016)](https://iopscience.iop.org/article/10.3847/0004-637X/825/1/73) found
0.164 ± 0.013 mag/century of dimming in Boyajian's Star using DASCH. Hippke et al. and Lund
et al. argued it was [systematics — specifically the "Menzel Gap" of the 1950s](https://www.centauri-dreams.org/2016/01/27/kic-8462852-no-dimming-after-all/),
when Harvard's programme changed and left a discontinuity. The DASCH team disputes that.
**It is still unresolved a decade later.**

So the failure mode is precisely: *a systematic step looks like a real long-term trend.*
(The same Michael Hippke wrote `wotan` and `transitleastsquares`, whose behaviour notebook 03
measures.)

**Odds.** Producing a defensible century-baseline light curve for an object nobody has
checked: good. Producing a *believed* claim of secular change: hard, precisely because of the
above.

**First step.** Do not hunt new trends. Try to **reproduce the Boyajian's Star dispute** —
both sides published, so there is ground truth on a contested question. Getting to a defended
opinion on who is right builds the exact systematics intuition the dataset demands. Before
even that: pull a DASCH light curve for a star we already understand and look at what 110
years of plates actually looks like.

---

## Not yet researched

Parked here so they are not lost. None of these have had a session spent on them.

- **Eclipsing binary eclipse-timing variations** — same machinery as idea 1, applied to a much
  less picked-over population, hunting third bodies. Needs a coverage check.
- **Asteroid rotation periods.** A [TESS survey](https://iopscience.iop.org/article/10.3847/1538-3881/acf194/meta)
  detected 37,965 asteroids but produced only 3,492 reliable periods, leaving 7,277 partial.
  The specific gap is **slow rotators** (P > 100 h), near-impossible from the ground. The
  *Minor Planet Bulletin* publishes amateur rotation periods routinely — the lowest barrier to
  a real citable result of anything found so far.
- **The TESS full-frame-image sky for everything that is not a planet** — flares, rotators,
  pulsators, AGN. [TESSELLATE](https://arxiv.org/pdf/2502.16905) suggests this is warming up.

## Ruled out

- **Gravitational waves** — public data, deeply specialised analysis, no room to add value.
- **Exoplanet atmospheres** — requires JWST time.
- **Anything hinging on novel statistics** — the one place AI assistance actively hurts.
- **Hot Jupiter transit timing** — 8,667 measurements deep already.
