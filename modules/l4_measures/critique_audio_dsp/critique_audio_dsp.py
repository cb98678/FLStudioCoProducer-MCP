from __future__ import annotations

from coproducer import call
from coproducer.result import Result, ok

_ORDER = {"high": 0, "medium": 1, "low": 2}


def _note(area: str, severity: str, message: str, **evidence) -> dict:
    return {"area": area, "severity": severity, "message": message, "evidence": evidence}


def _level_notes(r: dict, target: float, ceiling: float) -> list:
    out, tp, lufs, crest = [], r["true_peak"]["true_peak_dbtp"], r["loudness"]["lufs"], r["crest"]["crest_db"]
    if tp > ceiling:
        out.append(_note("peaks", "high", "True peak is above the %.1f dBTP ceiling." % ceiling, true_peak_dbtp=tp))
    if r["clipping"]["clipped_samples"] > 0:
        out.append(_note("clipping", "high", "Samples are clipped.", **r["clipping"]))
    if abs(lufs - target) > 3:
        out.append(_note("loudness", "medium", "Loudness is %.1f LU %s the %.1f LUFS target." % (abs(lufs - target), "above" if lufs > target else "below", target), lufs=lufs))
    if crest < 6:
        out.append(_note("dynamics", "medium", "Very low crest factor: the track is heavily compressed or limited.", crest_db=crest))
    return out


def _tone_notes(r: dict) -> list:
    b, out = r["bands"], []
    if b["sub"] - b["bass"] > 6:
        out.append(_note("low end", "medium", "Sub energy is far above the bass band; the low end may feel boomy or untranslatable.", sub_db=b["sub"], bass_db=b["bass"]))
    if r["centroid"]["centroid_hz"] < 400:
        out.append(_note("tone", "low", "The spectrum is very dark; there is little energy above the bass.", centroid_hz=r["centroid"]["centroid_hz"]))
    if r["silence"]["mostly_silent"]:
        out.append(_note("signal", "high", "The file is mostly silent.", **{k: r["silence"][k] for k in ("silent_fraction",)}))
    return out


def _stereo_notes(r: dict) -> list:
    out = []
    if "correlation" in r and r["correlation"]["correlation"] < 0.3:
        sev = "high" if r["correlation"]["correlation"] < 0 else "medium"
        out.append(_note("stereo", sev, "Low stereo correlation: phase problems or a very wide image; check mono.", **r["correlation"]))
    if "low_end_mono" in r and not r["low_end_mono"]["mono_below_cutoff"]:
        out.append(_note("low end", "medium", "Low frequencies are not centered; sub and bass should be close to mono.", **r["low_end_mono"]))
    return out


def critique_audio_dsp(path: str, loudness_target_lufs: float = -14.0, peak_ceiling_db: float = -1.0) -> Result:
    """Rule-based critique from measurements, used when the audio-language model is absent. Most severe findings come first.

    This checks levels, clipping, balance and stereo health. It cannot judge taste, groove or arrangement.
    """
    rep = call("build_measure_report", path=path)
    if not rep.ok:
        return rep
    notes = _level_notes(rep.value, loudness_target_lufs, peak_ceiling_db) + _tone_notes(rep.value) + _stereo_notes(rep.value)
    notes.sort(key=lambda n: _ORDER[n["severity"]])
    return ok({"observations": notes, "source": "dsp", "count": len(notes)})
