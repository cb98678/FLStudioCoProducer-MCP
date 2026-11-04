from __future__ import annotations

import json
from pathlib import Path

import time

from coproducer import call
from coproducer.result import Result, fail, ok
from coproducer.services import get_service

DEFAULTS = {"division": 4, "max_move_s": 0.1, "min_share": 0.7, "indices": []}


def _residual(path: str, bpm: float, division: int, lead: float) -> dict:
    """How far the syllables of a file still sit from where they should (ms): the marker detector's own onsets plus the lead against the
    grid lines (with lead 0, from the lines themselves)."""
    r = call("detect_warp_markers", path=path, bpm=bpm, division=division, lead_s=lead, max_move_s=0.1)
    if not r.ok:
        return {"markers": 0, "median_ms": None}
    moves = sorted(abs(m - g) * 1000.0 for m, g in zip(r.value["markers"], r.value["grid"]))
    med = moves[len(moves) // 2] if moves else None
    return {"markers": len(moves), "median_ms": (round(med, 1) if med is not None else None), "within_10ms": sum(1 for v in moves if v <= 10.0)}


def _titles() -> list[str]:
    got = call("list_open_dialogs")
    return [d["title"].lower() for d in got.value["dialogs"]] if got.ok else []


def _close_newtime() -> None:
    """Leave a failed chunk cleanly: Escape closes a dialog sitting over the editor (Sample properties, Delete all markers), Newtime's own
    X closes the editor only when it is still open (an Escape too many closed the playlist, 2026-11-03), and F5 brings the playlist back
    when it went."""
    titles = _titles()
    for _ in range(2):
        if not any("warpcorrection" in t or "newtone" in t or "playlist" in t for t in titles) and titles:
            call("press_hotkey", keys=["esc"])
            time.sleep(0.5)
            titles = _titles()
    if any("warpcorrection" in t for t in titles):
        call("run_gui_recipe", name="newtime_close_gui", params={})
        time.sleep(0.5)
    if not any("playlist" in t for t in _titles()):
        call("press_hotkey", keys=["f5"])
        time.sleep(0.8)


def _fit_one(c: dict, bpm: float, lead: float, passes: int, target_ms: float, o: dict) -> dict:
    src, p = Path(c["file"]), Path(c["file"])
    rec = {"index": c["index"], "lead_s": lead, "passes": [], "before": _residual(str(src), bpm, int(o["division"]), lead)}
    if not rec["before"]["markers"]:
        rec["skipped"] = "no syllable near a grid line"
        return rec
    if rec["before"]["median_ms"] is not None and rec["before"]["median_ms"] <= target_ms:
        rec["skipped"] = "already within %g ms" % target_ms
        return rec
    for n in range(1, passes + 1):
        out = p.with_name(p.stem + "_q%d" % n + p.suffix)
        r = call("quantize_vocal_gui", path=str(src), out_path=str(out), bpm=bpm, division=int(o["division"]), lead_s=lead,
                 max_move_s=float(o["max_move_s"]), min_share=float(o["min_share"]))
        if not r.ok:
            rec["passes"].append({"pass": n, "error": r.error.code, "message": r.error.message})
            _close_newtime()
            break
        after = _residual(str(out), bpm, int(o["division"]), lead)
        rec["passes"].append({"pass": n, "markers": r.value["markers"], "verified": r.value["verified"], "after": after})
        src = out
        if after["median_ms"] is not None and after["median_ms"] <= target_ms:
            break
    if rec["passes"] and "after" in rec["passes"][-1]:
        final = p.with_name(p.stem + "_q" + p.suffix)
        final.write_bytes(Path(src).read_bytes())
        rec["out"], rec["after"] = str(final), rec["passes"][-1]["after"]
    return rec


def quantize_vocal_chunks_gui(manifest_path: str, lead_s: float = -1.0, passes: int = 2, target_ms: float = 10.0, options: dict | None = None) -> Result:
    """Fit every chunk of a vocal manifest (split_vocal_phrases) to the beat with FL's Newtime, one short file at a time in the open bench
    project: quantize_vocal_gui per chunk (its file starts on a grid line, so Newtime's grid is the song's), the syllables' remaining
    distance from the lines measured after each pass (detect_warp_markers' own onsets), another pass while the median is over target_ms,
    the last pass copied to STEM_NN_q.wav for join_vocal_chunks. lead_s negative keeps the manifest's lead (the feel), 0 puts the syllables
    on the lines. options: division (4), max_move_s (0.1), min_share (0.7), indices (only these chunks). A chunk already within target_ms
    or with no syllable near a line is skipped; one whose fit fails is closed and reported. Errors: E_SANDBOX_VIOLATION, E_IO, E_HALTED.
    """
    root = str(get_service("sandbox_root"))
    mp = call("check_sandbox_path", path=manifest_path, sandbox_root=root)
    if not mp.ok:
        return mp
    try:
        man = json.loads(Path(mp.value["resolved"]).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return fail("E_IO", "cannot read the manifest: %s" % e)
    o = {**DEFAULTS, **(options or {})}
    lead = float(man.get("lead_s", 0.0)) if lead_s < 0 else float(lead_s)
    want = set(int(i) for i in o["indices"]) if o["indices"] else None
    fits = {str(f["index"]): f for f in man.get("fit", [])}
    for c in man["chunks"]:
        if want is not None and c["index"] not in want:
            continue
        rec = _fit_one(c, float(man["bpm"]), lead, int(passes), float(target_ms), o)
        fits[str(c["index"])] = rec
        man["fit"] = [fits[k] for k in sorted(fits, key=int)]
        Path(mp.value["resolved"]).write_text(json.dumps(man, indent=1), encoding="utf-8")
        if rec["passes"] and rec["passes"][-1].get("error") == "E_HALTED":
            return fail("E_HALTED", "stopped at chunk %d" % c["index"], fit=man["fit"])
    done = [f for f in man["fit"] if "out" in f]
    meds = sorted(f["after"]["median_ms"] for f in done if f["after"]["median_ms"] is not None)
    return ok({"fitted": len(done), "skipped": [f["index"] for f in man["fit"] if "skipped" in f],
               "failed": [{"index": f["index"], "error": f["passes"][-1].get("error")} for f in man["fit"] if f["passes"] and "error" in f["passes"][-1]],
               "median_after_ms": (meds[len(meds) // 2] if meds else None), "manifest": mp.value["resolved"]})
