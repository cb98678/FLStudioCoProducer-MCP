"""Close the mixing loop on a sandbox project: listen, apply the brain's master gain and EQ proposals, render again, and check the audio moved the way each proposal said.

A local model's numbers are not trusted on their own: the gain direction is checked against the loudness, every change is capped, and each EQ move
must show up in the bands it targets (calibrated 2026-10-20: FL's mixer EQ moves a band about 28 dB per unit of value, linear, 0.5 is flat).
"""
from __future__ import annotations

import json
from pathlib import Path

from . import eq_cmd, probe_cmd as p

DB_PER_UNIT = 28.0
MAX_EQ_DB = 6.0
EQ_TARGETS = {"low": (0, ("sub", "bass")), "mid": (1, ("mid", "high_mid")), "high": (2, ("presence", "air"))}
SEEN_FRACTION = 0.5          # a move counts as heard when at least this share of the requested dB shows up in its bands


def eq_db_to_value(db: float) -> float:
    """The 0 to 1 value FL's mixer EQ takes for a dB change from flat."""
    return min(1.0, max(0.0, 0.5 + db / DB_PER_UNIT))


def eq_moves(proposals: list) -> list:
    """Valid EQ proposals as (band, db) with db capped, one per band (the first one wins)."""
    moves, seen = [], set()
    for pr in proposals:
        if pr.get("valid") and pr.get("name") == "adjust_eq_band":
            a = json.loads(pr["arguments"])
            if a["band"] in EQ_TARGETS and a["band"] not in seen:
                seen.add(a["band"])
                moves.append((a["band"], max(-MAX_EQ_DB, min(MAX_EQ_DB, float(a["db"])))))
    return moves


def gain_move(proposals: list):
    """The first valid master gain proposal whose direction suits the loudness, or None."""
    for pr in proposals:
        if pr.get("valid") and pr.get("name") == "adjust_master_gain" and pr.get("direction_ok") is not False:
            return float(json.loads(pr["arguments"])["db"])
    return None


def eq_effect(before: dict, after: dict, band: str, gain_db: float) -> float:
    """Largest change of the bands a move targets, in dB, after taking the master gain change out."""
    d = eq_cmd.band_deltas(before, after)
    vals = [d[k] - gain_db for k in EQ_TARGETS[band][1] if k in d]
    return max(vals, key=abs) if vals else 0.0


def heard(want_db: float, effect_db: float) -> bool:
    return want_db * effect_db > 0 and abs(effect_db) >= SEEN_FRACTION * abs(want_db)


def _apply_eq(call, out: dict, moves: list, originals: dict) -> bool:
    for band, db in moves:
        idx = EQ_TARGETS[band][0]
        cur = call("op_mixer_get_eq_gain", index=0, band=idx)
        if not cur.ok:
            return p_step(out, "eq_" + band, cur)
        originals[idx] = cur.value
        if not p_step(out, "eq_" + band, call("set_eq_gain_verified", index=0, band=idx, value=eq_db_to_value((cur.value - 0.5) * DB_PER_UNIT + db)), requested_db=db):
            return False
    return True


def p_step(out: dict, name: str, r, **extra) -> bool:
    out["steps"][name] = {"ok": r.ok, **({"error": "%s %s" % (r.error.code, r.error.message)} if not r.ok else {}), **extra}
    return r.ok


def _restore(call, out: dict, project: Path, fader_db, originals: dict) -> None:
    if fader_db is not None:
        p_step(out, "restore_fader", call("set_track_volume_db_verified", index=0, db=fader_db))
    for idx, val in originals.items():
        call("set_eq_gain_verified", index=0, band=idx, value=val)
    p_step(out, "restore_save", call("save_sandbox_project", project=str(project)))


def _judge(out: dict, before: dict, after: dict, moves: list, applied_gain: float) -> None:
    out["loudness"] = {"before": p._lufs(before), "after": p._lufs(after), "applied_gain_db": round(applied_gain, 2)}
    out["eq_checks"] = {}
    if not moves and applied_gain:
        moved = p._lufs(after) - p._lufs(before)
        out["gain_check"] = {"applied_db": round(applied_gain, 2), "moved_lu": round(moved, 2), "ok": abs(moved - applied_gain) <= 1.0}
    for band, db in moves:
        eff = eq_effect(before, after, band, applied_gain)
        out["eq_checks"][band] = {"requested_db": db, "measured_db": round(eff, 2), "heard": heard(db, eff)}


def _passed(out: dict) -> bool:
    return all(v["ok"] for v in out["steps"].values()) and bool(out.get("eq_checks", {}) or out["plan"]["gain_db"] is not None) \
        and all(c["heard"] for c in out.get("eq_checks", {}).values()) and out.get("gain_check", {"ok": True})["ok"]


def _apply_all(call, out: dict, project: Path, work: Path, before: dict, gain, moves: list, state: dict) -> bool:
    """Apply gain and EQ, save, render, measure and judge. state collects what must be put back. False at the first failing step."""
    if gain is not None:
        trim = call("apply_gain_trim", index=0, delta_db=gain, max_delta_db=6.0)
        if not p_step(out, "apply_gain", trim):
            return False
        state["fader"], state["applied"] = trim.value["before_db"], trim.value["applied_delta_db"]
    if not _apply_eq(call, out, moves, state["eq"]) or not p_step(out, "save", call("save_sandbox_project", project=str(project))):
        return False
    r = call("render_with_restart", project=str(project), out_dir=str(work / "after"))
    m = call("build_measure_report", path=r.value["path"]) if r.ok else r
    if not (p_step(out, "render_after", r) and p_step(out, "measure_after", m)):
        return False
    _judge(out, before, m.value, moves, state["applied"])
    out["after_report"] = m.value
    return True


def polish(call, project: Path, work: Path, bpm: float = 128.0, keep: bool = False, keep_if_heard: bool = False) -> dict:
    """Listen, apply the brain's usable proposals to the master, render again and check each change.

    Everything is put back unless keep is true, or keep_if_heard is true and every check passed (the sandbox copy then holds the better mix).
    """
    project, work, out = Path(project), Path(work), {"steps": {}}
    first = p.listen(call, project, work / "before", bpm)
    out["steps"].update(first["steps"])
    if not first.get("report"):
        return {**out, "passed": False}
    before, props = first["report"], first.get("proposals", [])
    out.update({k: first[k] for k in ("audio", "report", "listener_notes") if k in first})
    gain, moves = gain_move(props), eq_moves(props)
    out["proposals"], out["plan"] = props, {"gain_db": gain, "eq": moves}
    if gain is None and not moves:
        if not props:                  # the brain found nothing to change: the project is untouched and that is a pass
            out["steps"]["proposals"] = {"ok": True, "note": "the brain proposed no change"}
            return {**out, "passed": True, "kept": False}
        out["steps"]["proposals"] = {"ok": False, "error": "nothing usable to apply (no valid, right-direction gain or EQ proposal)"}
        return {**out, "passed": False}
    state = {"fader": None, "applied": 0.0, "eq": {}}
    try:
        _apply_all(call, out, project, work, before, gain, moves, state)
    finally:
        out["passed"] = _passed(out)
        out["kept"] = keep or (keep_if_heard and out["passed"])
        if not out["kept"]:
            _restore(call, out, project, state["fader"], state["eq"])
    return out
