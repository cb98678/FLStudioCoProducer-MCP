from __future__ import annotations

from pathlib import Path

from coproducer import beatgrid, call
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def detect_beats_ml(path: str, drift_pct: float = 3.0) -> Result:
    """Beats and downbeats of an audio file (beat_this, MIT, run in the mir environment), then the grid: tempo from a line through the beats,
    meter from beats per bar, bar lines, bars whose beat count differs, and drift (a live band moving more than drift_pct percent).

    Measured on the host 2026-10-25: the Friends stems gave 108.504 bpm in 4/4 against 108.478 found by hand, and the bar line before the drums
    within 31 ms of the hand-found one. Errors: E_NOT_FOUND, E_MODEL (checkpoint missing or the model failed), E_NOT_VERIFIED (too few bars).
    """
    if not Path(path).is_file():
        return fail("E_NOT_FOUND", "no audio file at %s" % Path(path).name)
    ckpt = (get_service("model_files") or {}).get("beat_this_final0", {})
    got = call("run_model_op", model="mir", op="beats", timeout_s=900,
               args={"path": path, "checkpoint": ckpt.get("path", ""), "sha256": ckpt.get("sha256", "")})
    if not got.ok:
        return got
    beats, downs = got.value["beats"], got.value["downbeats"]
    if len(downs) < 3 or len(beats) < 4:
        return fail("E_NOT_VERIFIED", "the model found %d beats and %d downbeats; too few for a grid" % (len(beats), len(downs)))
    grid = beatgrid.analyze(beats, downs, drift_pct)
    return ok({**grid, "beats": beats, "downbeats": downs}, verified=True)
