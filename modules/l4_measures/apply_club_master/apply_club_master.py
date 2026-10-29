from __future__ import annotations

import json
import tomllib
from pathlib import Path

import soundfile as sf

from coproducer import call, mastering, tonal
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def apply_club_master(path: str, targets_file: str, out_path: str, lufs: float = 0.0, profile: str = "", match_amount: float = 0.7) -> Result:
    """Master a mixdown WAV to the targets' loudness and true-peak ceiling (lufs overrides). First: DC removed, lows under the targets'
    low_end_mono_below_hz made mono, a silent tail cut, and with a reference profile a broad linear-phase EQ toward the references' tonal
    balance (only what lies outside their spread, times match_amount). Then gain into a soft clipper and a look-ahead limiter on the oversampled
    peak, iterated to the loudness, stopping at the crest floor instead of squashing; measured again independently; 24-bit WAV.
    Errors: E_SANDBOX_VIOLATION, E_NOT_FOUND, E_ARG, E_NOT_VERIFIED (see "stopped").
    """
    chk = call("check_sandbox_path", path=out_path, sandbox_root=str(get_service("sandbox_root")))
    if not chk.ok:
        return chk
    if not Path(path).is_file() or not Path(targets_file).is_file():
        return fail("E_NOT_FOUND", "need the mixdown and the targets file")
    t = tomllib.loads(Path(targets_file).read_text(encoding="utf-8"))
    loud, dyn = t.get("loudness", {}), t.get("dynamics", {})
    if "integrated_lufs" not in loud or "true_peak_dbtp_ceiling" not in loud:
        return fail("E_ARG", "the targets file has no [loudness] integrated_lufs and true_peak_dbtp_ceiling")
    x, rate = sf.read(path, dtype="float64", always_2d=True)
    x, cleaned = mastering.prepare(x, rate, mono_below_hz=float(t.get("stereo", {}).get("low_end_mono_below_hz", 0) or 0))
    want = lufs or float(loud["integrated_lufs"])
    tone = None
    if profile:
        if not Path(profile).is_file():
            return fail("E_NOT_FOUND", "no reference profile at %s" % Path(profile).name)
        prof = json.loads(Path(profile).read_text(encoding="utf-8"))["tonal"]
        own = tonal.band_levels(x, rate)
        gains = tonal.match_gains(own, prof, amount=match_amount)
        x = tonal.apply_eq(x, rate, gains)
        tone = {"gains_db": gains, "before": tonal.deviation(own, prof), "prof": prof}
    r = mastering.master(x, rate, want, float(loud["true_peak_dbtp_ceiling"]), float(dyn.get("crest_factor_db", {}).get("min", 6.5)))
    Path(chk.value["resolved"]).parent.mkdir(parents=True, exist_ok=True)
    sf.write(chk.value["resolved"], r.pop("audio").astype("float32"), rate, subtype="PCM_24")
    out = chk.value["resolved"]
    meas = {"lufs": call("measure_integrated_loudness", path=out), "tp": call("measure_true_peak", path=out), "crest": call("measure_crest_factor", path=out)}
    if not all(m.ok for m in meas.values()):
        return next(m for m in meas.values() if not m.ok)
    got = {"lufs": meas["lufs"].value["lufs"], "true_peak_dbtp": meas["tp"].value["true_peak_dbtp"], "crest_db": meas["crest"].value["crest_db"]}
    if tone:
        y, _ = sf.read(out, dtype="float64", always_2d=True)
        tone = {"gains_db": tone["gains_db"], "before": tone["before"], "after": tonal.deviation(tonal.band_levels(y, rate), tone.pop("prof"))}
    tol = float(loud.get("integrated_tolerance_lu", 1.0))
    agree = abs(got["lufs"] - r["lufs"]) < 0.3 and got["true_peak_dbtp"] <= float(loud["true_peak_dbtp_ceiling"]) + 0.15
    on_target = abs(got["lufs"] - want) <= tol
    return ok({"out": out, "target_lufs": want, "loop": r, "measured": got, "on_target": on_target, "stopped": r["stopped"], "tonal": tone, "cleaned": cleaned},
              verified=agree and on_target)
