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

__all__ = ["transit_model", "a_rs_from_duration"]


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
