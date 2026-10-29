from __future__ import annotations

import tomllib
from pathlib import Path

from coproducer.datafiles import find_unfilled, missing_keys
from coproducer.result import Result, fail, ok

# targets key -> (path in the measure report, kind)
MAP = {"loudness.integrated_lufs": ("loudness.lufs", "value"), "dynamics.crest_factor_db": ("crest.crest_db", "range"),
       "loudness.true_peak_dbtp_ceiling": ("true_peak.true_peak_dbtp", "max"), "loudness.loudness_range_lu": ("range.lra_lu", "range"),
       "stereo.correlation_floor": ("correlation.correlation", "min"), "stereo.low_end_side_over_mid_db_max": ("low_end_mono.side_over_mid_db", "max"),
       "clipping.max_clipped_samples": ("clipping.clipped_samples", "max"), "dc.max_offset_dbfs": ("dc.max_dbfs", "max")}


def _dig(d: dict, dotted: str):
    for part in dotted.split("."):
        d = d.get(part) if isinstance(d, dict) else None
    return d


def _limit(key: str, v, data: dict) -> dict:
    path, kind = MAP[key]
    tol = _dig(data, "loudness.integrated_tolerance_lu") or 0
    span = {"value": lambda: {"min": v - tol, "max": v + tol}, "range": lambda: {"min": v["min"], "max": v["max"]},
            "max": lambda: {"max": v}, "min": lambda: {"min": v}}[kind]()
    return {"label": key, "path": path, **span}


def load_targets_file(path: str) -> Result:
    """Read a targets TOML file and turn it into limits on the measure report. Refuses files that still contain FILL blanks.

    Errors: E_NOT_FOUND, E_IO for bad TOML, E_ARG listing the blanks (targets are chosen by a person, never invented).
    """
    f = Path(path)
    if not f.is_file():
        return fail("E_NOT_FOUND", "no targets file at %s" % path)
    try:
        data = tomllib.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return fail("E_IO", "cannot read targets: %s" % e)
    blanks = find_unfilled(data)
    if blanks:
        return fail("E_ARG", "the targets file still has %d blank value(s); a person must fill them" % len(blanks), unfilled=blanks)
    gone = missing_keys(data, {"meta": {"name": 1}})
    limits = [_limit(k, _dig(data, k), data) for k in MAP if _dig(data, k) is not None]
    return ok({"name": data["meta"]["name"] if not gone else f.stem, "source": _dig(data, "meta.source"), "limits": limits,
               "spectrum": data.get("spectrum", {}), "contrast": data.get("contrast", {})})
