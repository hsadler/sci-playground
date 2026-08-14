"""skyplay — shared helpers for the sci-playground notebooks.

The notebooks are the narrative; this package is the machinery they call, so that
logic used more than once lives in one place, gets tested, and can be fixed once.

Typical use::

    from skyplay import data, detrend, periods, plotting, vetting

    plotting.use_style()
    lc = data.load_stitched("kepler-8")               # cached after the first run
    flat, trend = detrend.biweight_flatten(lc, window_days=0.5)
    found = periods.tls_search(flat, period_min=1, period_max=10)
    print(found.summary())

    report = vetting.vet(flat.time.value, flat.flux.value, found.period, found.epoch)
    print(report.summary())

Import the submodules rather than pulling names into this namespace: importing
`skyplay.periods` pays for lightkurve, and `skyplay.models` for batman, only when
you actually use them.
"""

from __future__ import annotations

import warnings

# lightkurve warns at import time that its `tpfmodel` submodule is unavailable without
# `oktopus`. That is an optional dependency used only for fitting PRF (pixel response
# function) models to individual pixels -- nothing here does that, and oktopus is
# unmaintained against current Python. The warning is pure noise, and alarming noise to
# meet on your second notebook, so silence exactly that one message.
#
# Deliberately narrow: matched on the message text, so any *other* UserWarning from
# lightkurve still reaches you. This runs before any submodule imports lightkurve.
warnings.filterwarnings(
    "ignore",
    message=".*tpfmodel submodule is not available.*",
    category=UserWarning,
)

__version__ = "0.1.0"

__all__ = [
    "cache",
    "data",
    "detrend",
    "injection",
    "models",
    "periods",
    "plotting",
    "synthetic",
    "vetting",
]
