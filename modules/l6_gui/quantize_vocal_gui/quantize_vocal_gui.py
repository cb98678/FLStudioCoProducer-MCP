from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok
from coproducer.services import get_service

SNAP_ROW = {1: 1, 2: 2, 3: 3, 4: 4, 6: 5, 8: 6}     # Newtime's Snap menu: Beat, 1/2, 1/3, 1/4, 1/6, 1/8 beat
MIN_SHARE = 0.8


def quantize_vocal_gui(path: str, out_path: str, bpm: float, division: int = 4, lead_s: float = -1.0, grid_up: int = 442,
                       grid_down: int = 441) -> Result:
    """Fit a vocal to the beat with FL's Newtime and save it: warp markers at its own syllable onsets, quantized to 1/division beat.

    The vocal is first slowed by grid_up/grid_down onto Newtime's grid (here it draws bpm as if the samples ran at 44200 Hz) and sped back
    after. Steps: prepare_rate_copy, detect_warp_markers, newtime_load_gui, add_warp_markers_gui, newtime_quantize_save_gui, prepare_rate_copy.
    Errors: E_ARG, E_SANDBOX_VIOLATION, E_IO, E_GUI_MISMATCH, E_NOT_VERIFIED (under 80 % of the markers seen placed), E_HALTED.
    """
    if division not in SNAP_ROW:
        return fail("E_ARG", "division must be one of %s" % sorted(SNAP_ROW))
    root = str(get_service("sandbox_root"))
    src, dst = call("check_sandbox_path", path=path, sandbox_root=root), call("check_sandbox_path", path=out_path, sandbox_root=root)
    if not src.ok or not dst.ok:
        return src if not src.ok else dst
    stem = dst.value["resolved"].rsplit(".", 1)[0]
    slow = call("prepare_rate_copy", path=src.value["resolved"], out_path=stem + "_newtime_in.wav", up=grid_up, down=grid_down)
    if not slow.ok:
        return slow
    grid_bpm = bpm * grid_down / grid_up
    plan = call("detect_warp_markers", path=slow.value["out_path"], bpm=grid_bpm, division=division, lead_s=lead_s)
    opened = call("run_gui_recipe", name="newtime_load_gui", params={"path": slow.value["out_path"], "bpm": "%g" % bpm}) if plan.ok else plan
    if not opened.ok:
        return opened
    p = plan.value
    placed = call("add_warp_markers_gui", markers=p["markers"], duration_s=p["duration_s"], bpm=grid_bpm, peaks_5ms=p["peaks_5ms"])
    if not placed.ok:
        return placed
    if placed.value["verified"] < MIN_SHARE * len(p["markers"]):
        return fail("E_NOT_VERIFIED", "only %d of %d warp markers were seen in Newtime; nothing was quantized" % (placed.value["verified"], len(p["markers"])),
                    missed=placed.value["missed"], skipped=placed.value["skipped"])
    saved = call("run_gui_recipe", name="newtime_quantize_save_gui", params={"out_path": stem + "_newtime_out.wav", "snap_row": SNAP_ROW[division]})
    back = call("prepare_rate_copy", path=stem + "_newtime_out.wav", out_path=dst.value["resolved"], up=grid_down, down=grid_up) if saved.ok else saved
    if not back.ok:
        return back
    return ok({"out_path": dst.value["resolved"], "markers": len(p["markers"]), "verified": placed.value["verified"], "lead_s": p["lead_s"],
               "mean_move_ms": p["mean_move_ms"], "onsets": p["onsets"], "grid_bpm": round(grid_bpm, 4)})
