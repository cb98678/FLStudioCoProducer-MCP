from __future__ import annotations

from coproducer import dsp
from coproducer.result import Result, fail, ok


def estimate_bpm_dsp(path: str, min_bpm: float = 60.0, max_bpm: float = 200.0, hint_bpm: float = 0.0) -> Result:
    """Estimate tempo from audio with DSP: best guess, ranked candidates, an `ambiguous` flag and the `relatives` behind it.

    A 2:1 or 3:2 relative can outscore the real tempo (128 BPM techno gave 64.0), so `ambiguous` is true when the runner-up
    is within 10 percent or a 2:1 or 3:2 relative has real strength. Then pass hint_bpm (the project tempo; the candidate
    within 6 percent wins) or narrow min_bpm and max_bpm to the genre range. Errors: E_ARG when too short or no pulse.
    """

    try:
        x, rate = dsp.load_audio(path, 90.0)
    except ValueError as e:
        return fail("E_IO", str(e))
    found = dsp.estimate_tempo(x, rate, min_bpm, max_bpm)
    if not found:
        return fail("E_ARG", "no tempo found: the audio is too short or has no clear pulse")
    cands = [{"bpm": float(c["bpm"]), "strength": float(c["strength"])} for c in found]
    best = cands[0]
    amb = dsp.tempo_ambiguity(cands)
    out = {"candidates": cands, "ambiguous": amb["ambiguous"], "relatives": amb["relatives"]}
    if hint_bpm:
        near = [c for c in cands if abs(c["bpm"] - hint_bpm) <= 0.06 * hint_bpm]
        out["matched_hint"] = bool(near)
        best = min(near, key=lambda c: abs(c["bpm"] - hint_bpm)) if near else best
    out["bpm"] = best["bpm"]
    return ok(out)
