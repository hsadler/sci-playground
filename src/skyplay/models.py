"""Physically real transit shapes, via batman.

`skyplay.synthetic.trapezoid_transit` is a cartoon with straight edges. A real
transit differs in two ways that matter once you start fitting:

- **Limb darkening.** A star is not a uniform disc; its edge is dimmer than its
  centre. So a planet crossing the middle blocks proportionally more light than one
  crossing the limb, which rounds the floor of the transit into a curve rather than
  a flat line. This is also why the observed central depth is *deeper* than
  (Rp/Rs)**2.
- **Geometry.** Ingress and egress are curved, and their duration depends on the
  impact parameter — how far from the star's centre the planet crosses.

batman implements the Mandel & Agol (2002) analytic model. Use it when you want to
fit a real depth or radius rather than eyeball one.

Note ``a_rs`` — the orbital distance in units of *stellar radii*, not AU. It sets
the transit duration for a given period, and it is where a fit most often goes
wrong, because it is degenerate with inclination.
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "transit_model",
    "a_rs_from_duration",
    "a_rs_from_density",
    "transit_duration",
    "planet_radius_earth",
]

#: Mean density of the Sun, kg/m^3. Stellar densities below are quoted relative to it.
SOLAR_DENSITY = 1408.0


def transit_model(
    t: np.ndarray,
    *,
    period: float,
    t0: float,
    rp_rs: float,
    a_rs: float,
    inc: float = 90.0,
    ecc: float = 0.0,
    omega: float = 90.0,
    u: tuple[float, ...] = (0.3, 0.2),
    limb_dark: str = "quadratic",
) -> np.ndarray:
    """Limb-darkened transit light curve.

    Parameters
    ----------
    t
        Times, in days, same scale as ``t0``.
    period
        Orbital period, days.
    t0
        A mid-transit time.
    rp_rs
        Planet radius in stellar radii.
    a_rs
        Semi-major axis in stellar radii. See `a_rs_from_duration` to get a
        starting value from an observed duration.
    inc
        Orbital inclination in degrees; 90 is edge-on (a central transit).
    ecc, omega
        Eccentricity and argument of periastron (degrees).
    u
        Limb-darkening coefficients matching ``limb_dark``. The default is a
        reasonable quadratic law for a Sun-like star in the Kepler band.
    limb_dark
        One of batman's laws: 'uniform', 'linear', 'quadratic', 'nonlinear', etc.

    Returns
    -------
    Normalized flux, 1.0 out of transit.
    """
    import batman

    params = batman.TransitParams()
    params.t0 = t0
    params.per = period
    params.rp = rp_rs
    params.a = a_rs
    params.inc = inc
    params.ecc = ecc
    params.w = omega
    params.u = list(u)
    params.limb_dark = limb_dark

    t = np.ascontiguousarray(np.asarray(t, dtype=float))
    return batman.TransitModel(params, t).light_curve(params)


def a_rs_from_density(period: float, density_solar: float = 1.0) -> float:
    """Semi-major axis in stellar radii, from the period and the star's mean density.

    Kepler's third law plus the definition of density collapses to something neat: the
    orbital distance in *stellar radii* depends only on the period and the star's mean
    density, not on its mass and radius separately::

        a/Rs = (G rho P^2 / 3pi)^(1/3)

    which for a Sun-density star is ``4.20 * (P/day)^(2/3)``.

    This is the workhorse behind transit modelling, and it runs both ways: measure a
    transit's duration and you have constrained the *density of the star*, which is why
    transit surveys double as stellar-characterisation surveys.
    """
    if period <= 0 or density_solar <= 0:
        raise ValueError("period and density_solar must be positive")

    from astropy import constants as const

    rho = density_solar * SOLAR_DENSITY
    period_seconds = period * 86400.0
    return float((const.G.value * rho * period_seconds**2 / (3.0 * np.pi)) ** (1.0 / 3.0))


def transit_duration(period: float, rp_rs: float = 0.0, density_solar: float = 1.0) -> float:
    """Duration of a central (edge-on) transit, in days.

    The planet crosses a chord of ``2(1 + Rp/Rs)`` stellar radii while covering the whole
    orbit in ``period``, so::

        duration = period / pi * (1 + Rp/Rs) / (a/Rs)

    A non-central transit crosses a shorter chord and lasts less, so treat this as the
    maximum for a given period and density. For a hot Jupiter at 3.5 d around a Sun-like
    star it gives ~3 hours, which is the right ballpark.
    """
    a_rs = a_rs_from_density(period, density_solar)
    return float(period / np.pi * (1.0 + rp_rs) / a_rs)


def a_rs_from_duration(period: float, duration: float, rp_rs: float = 0.0) -> float:
    """Estimate a/Rs from an observed transit duration, assuming a central transit.

    For a circular, edge-on orbit the planet crosses a chord of length
    2(1 + Rp/Rs) stellar radii, and it covers the full orbit in ``period``, so::

        duration / period = (1 + Rp/Rs) / (pi * a/Rs)

    which rearranges to the expression below. This is only a starting guess: any
    non-central transit crosses a shorter chord, so a real (inclined) system needs
    a larger a/Rs than this returns. Feed it to a fitter, do not report it.
    """
    if duration <= 0 or period <= 0:
        raise ValueError("period and duration must be positive")
    return float((1.0 + rp_rs) * period / (np.pi * duration))


def planet_radius_earth(depth: float, stellar_radius_rsun: float) -> float:
    """Planet radius in Earth radii, from a transit depth and the star's radius.

    This is the conversion that turns a measurement into something you can care about.
    A depth is a *ratio* — it says how much light was blocked, not how big the blocker
    was — so the same dip means wildly different planets on different stars::

        Rp = sqrt(depth) * Rs

    A 500 ppm transit is a 3.6 Earth-radii planet on Kepler-8 (1.49 Rsun) and a 0.73
    Earth-radii planet on a 0.30 Rsun M dwarf. Identical data, identical pipeline,
    sub-Earth versus small-Neptune. That is the quantitative form of "small cool stars
    are the best transit targets".

    Two caveats, both of which make this an *upper* bound in practice:

    - **Dilution.** Extra light in the aperture makes the dip shallower than it truly is,
      so the real planet is larger than this returns (see `skyplay.vetting.dilute_depth`).
    - **Limb darkening.** The observed central depth runs deeper than the geometric
      ``(Rp/Rs)**2``, so feeding a measured central depth in here overestimates the radius
      slightly. Fitting a real model is the fix when it matters.

    And it inherits the uncertainty on ``stellar_radius_rsun``, which for most stars comes
    from a model rather than a direct measurement. A 10% error on the star is a 10% error
    on the planet.
    """
    if depth < 0:
        raise ValueError(f"depth must be non-negative, got {depth}")
    if stellar_radius_rsun <= 0:
        raise ValueError(f"stellar radius must be positive, got {stellar_radius_rsun}")

    from astropy import units as u

    rsun_in_rearth = (1 * u.Rsun).to_value(u.Rearth)
    return float(np.sqrt(depth) * stellar_radius_rsun * rsun_in_rearth)
