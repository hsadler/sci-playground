"""On-disk cache for *derived* light curves.

Lightkurve already caches raw MAST downloads under ``~/.lightkurve``. This module
caches the things you compute *from* those downloads — stitched, cleaned,
detrended curves — because re-running a four-quarter stitch on every kernel
restart is the fastest way to lose interest in a project.

Derived products live in ``data/cache/`` (gitignored) as Parquet, which round-trips
float columns exactly and is readable by anything.

Only time / flux / flux_err survive the round trip, along with enough metadata to
rebuild the astropy `Time` axis correctly. Per-cadence quality flags and the
original FITS headers do not. That is deliberate: if you need those, you want the
real file, not a cache. Cache derived curves, re-download originals.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from astropy import units as u
from astropy.time import Time
from lightkurve import LightCurve

__all__ = ["cache_dir", "save_lightcurve", "load_lightcurve", "cached"]

_METADATA_KEY = b"skyplay"


def cache_dir() -> Path:
    """The cache directory, created on first use.

    Resolved relative to the repo root (the parent of ``src/``) so it lands in the
    same place whether you are running from a notebook, a test, or the CLI.
    """
    root = Path(__file__).resolve().parents[2]
    path = root / "data" / "cache"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_lightcurve(lc: LightCurve, path: str | Path) -> Path:
    """Write a `LightCurve` to Parquet, preserving the time format and flux units."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    frame = pd.DataFrame(
        {
            "time": np.asarray(lc.time.value, dtype=float),
            "flux": np.asarray(lc.flux.value, dtype=float),
            "flux_err": np.asarray(lc.flux_err.value, dtype=float),
        }
    )
    meta = {
        "time_format": lc.time.format,
        "time_scale": lc.time.scale,
        "flux_unit": str(lc.flux.unit) if lc.flux.unit is not None else "",
        "label": lc.meta.get("LABEL") or lc.meta.get("OBJECT") or "",
        "mission": lc.meta.get("MISSION") or "",
    }

    table = pa.Table.from_pandas(frame, preserve_index=False)
    table = table.replace_schema_metadata(
        {**(table.schema.metadata or {}), _METADATA_KEY: json.dumps(meta).encode()}
    )
    pq.write_table(table, path, compression="zstd")
    return path


def load_lightcurve(path: str | Path) -> LightCurve:
    """Read back a `LightCurve` written by `save_lightcurve`."""
    table = pq.read_table(Path(path))
    raw = (table.schema.metadata or {}).get(_METADATA_KEY)
    meta = json.loads(raw) if raw else {}
    frame = table.to_pandas()

    time = Time(
        frame["time"].to_numpy(),
        format=meta.get("time_format", "bkjd"),
        scale=meta.get("time_scale", "tdb"),
    )
    unit = u.Unit(meta["flux_unit"]) if meta.get("flux_unit") else u.dimensionless_unscaled
    return LightCurve(
        time=time,
        flux=frame["flux"].to_numpy() * unit,
        flux_err=frame["flux_err"].to_numpy() * unit,
        meta={"LABEL": meta.get("label", ""), "MISSION": meta.get("mission", "")},
    )


def cached(key: str, build: Callable[[], LightCurve], refresh: bool = False) -> LightCurve:
    """Return the cached curve for ``key``, calling ``build()`` on a miss.

    ``key`` becomes a filename, so keep it filesystem-safe and *descriptive of
    every input that affects the result* — if you change the quarters you stitch
    but not the key, you will silently get the old curve back. Pass
    ``refresh=True`` to force a rebuild.
    """
    path = cache_dir() / f"{key}.parquet"
    if path.exists() and not refresh:
        return load_lightcurve(path)
    lc = build()
    save_lightcurve(lc, path)
    return lc
