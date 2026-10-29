"""Measure what FL's built-in mixer EQ does: set one band, save, render, and compare with a flat render.

The brain talks in dB and FL takes a 0 to 1 value (0.5 flat), so this finds out how far a value moves each band before any EQ proposal is applied.
Band energies in a report are relative to the total energy, so the change of the total (rms) is added back to get absolute dB per band.
"""
from __future__ import annotations

from pathlib import Path

from . import probe_cmd as p

BAND_NAMES = ("low", "mid", "high")


def _bands(report: dict) -> dict:
    return report.get("bands", {})


def _rms(report: dict):
    return report.get("crest", {}).get("rms_db")


def band_deltas(flat: dict, tested: dict) -> dict:
    """Absolute change in dB per measured band between two reports: the relative band change plus the change of the whole signal."""
    a, b = _bands(flat), _bands(tested)
    shift = (_rms(tested) - _rms(flat)) if _rms(flat) is not None and _rms(tested) is not None else 0.0
    return {k: round(b[k] - a[k] + shift, 2) for k in a if k in b}


def _render_measure(call, project: Path, work: Path, tag: str):
    r = call("render_with_restart", project=str(project), out_dir=str(work / tag))
    if not r.ok:
        return r, None
    m = call("build_measure_report", path=r.value["path"])
    return m, (m.value if m.ok else None)


def _one_point(call, project: Path, work: Path, track: int, band: int, value: float, flat: dict) -> dict:
    """Set one band to a value, save, render, measure, and describe the change against the flat render."""
    set_ = call("set_eq_gain_verified", index=track, band=band, value=value)
    if not set_.ok:
        return {"ok": False, "error": "%s %s" % (set_.error.code, set_.error.message)}
    saved = call("save_sandbox_project", project=str(project))
    if not saved.ok:
        return {"ok": False, "error": "save: %s %s" % (saved.error.code, saved.error.message)}
    res, rep = _render_measure(call, project, work, "band%d_%03d" % (band, round(value * 100)))
    if rep is None:
        return {"ok": False, "error": "render: %s" % (res.error.message if not res.ok else "no report")}
    d = band_deltas(flat, rep)
    return {"ok": True, "value": value, "absolute_db": d, "lufs_delta": round(p._lufs(rep) - p._lufs(flat), 2), "peak_db": max(d.values(), key=abs) if d else None}


def _flatten(call, project: Path, track: int):
    """Put all three bands to flat and save. Returns the first failing result, or None."""
    for b in (0, 1, 2):
        r = call("set_eq_gain_verified", index=track, band=b, value=0.5)
        if not r.ok:
            return r
    s = call("save_sandbox_project", project=str(project))
    return None if s.ok else s


def eq_calibration(call, project: Path, work: Path, track: int = 0, values: tuple = (0.65, 0.8)) -> dict:
    """Render flat, then each EQ band raised to each test value on its own, and report the absolute dB change per measured band. The EQ is put back flat."""
    project, work = Path(project), Path(work)
    out: dict = {"track": track, "values": list(values), "bands": {n: [] for n in BAND_NAMES}}
    bad = _flatten(call, project, track)
    if bad is not None:
        return {**out, "passed": False, "error": "%s %s" % (bad.error.code, bad.error.message)}
    res, flat = _render_measure(call, project, work, "flat")
    if flat is None:
        return {**out, "passed": False, "error": "flat render failed: %s" % (res.error.message if not res.ok else "no report")}
    out["flat_lufs"] = p._lufs(flat)
    try:
        for b in (0, 1, 2):
            for v in values:
                out["bands"][BAND_NAMES[b]].append(_one_point(call, project, work, track, b, v, flat))
            call("set_eq_gain_verified", index=track, band=b, value=0.5)
    finally:
        out["restore_save"] = call("save_sandbox_project", project=str(project)).ok
    out["passed"] = all(pt["ok"] for pts in out["bands"].values() for pt in pts) and out["restore_save"]
    return out
