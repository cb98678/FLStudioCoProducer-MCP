from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

from coproducer import call, soundbrief, wavetables
from coproducer.result import Result, fail, ok
from coproducer.services import get_service

FADE_S = 0.003


def _shape(x: np.ndarray, rate: int, role: str, opt: dict):
    """(cut, its pitch or None, report) after isolate and tune, or a failure: the pitched part of prepare_sampler_sound."""
    extra: dict = {}
    near = 440.0 * 2 ** ((float(opt["pitch_midi"]) - 69) / 12) if "pitch_midi" in opt else 0.0   # over a chord, a note can read as the chord's root
    f0 = (wavetables.note_pitch(x.mean(axis=1), rate, *((0.75 * near, 1.33 * near) if near else ()))
          if role in ("bass", "melodic") or opt.get("isolate") else None)
    if opt.get("isolate"):
        if not f0:
            return fail("E_NOT_FOUND", "no held pitch in the cut: isolate needs one note")
        cols = [wavetables.harmonic_isolate(x[:, c], rate, f0) for c in range(x.shape[1])]
        x = np.stack([c[0] for c in cols], axis=1)
        extra["isolation_db"] = max(c[1] for c in cols)
    tune = opt.get("tune")
    if f0 and tune is not None and tune is not False:   # onto the nearest semitone (true), or by a number of cents measured on a longer stretch
        midi = 69 + 12 * np.log2(f0 / 440.0)
        cents = float(100 * (round(midi) - midi)) if tune is True else float(tune)
        x, f0 = wavetables.retune(x, 2 ** (cents / 1200)), f0 * 2 ** (cents / 1200)
        extra["tuned_cents"] = round(cents, 1)
    if f0:
        b = wavetables.bend_profile(x.mean(axis=1), rate, f0)
        extra["bend"] = {k: b[k] for k in ("head_cents", "tail_cents", "range_cents", "voiced_s")}
    return x, f0, extra


def prepare_sampler_sound(path: str, out_path: str, role: str, start_s: float = 0.0, end_s: float = 0.0, options: dict | None = None) -> Result:
    """Cut path (start_s to end_s, the whole file by default) into out_path, a 24-bit WAV in the sandbox with 3 ms fades, for Serum 2's
    sample oscillator or FL's Sampler; it plays at its own pitch on note 60 (FL's C5). options: target_midi (note 60 plays as that note),
    isolate (one synth note lifted out of a mix: only its harmonics kept, isolation_db is what was taken out), pitch_midi (the note it is,
    from a transcription: over a chord the search can land on its root), tune (true: onto the nearest semitone; cents: by that much), fade_out_s.
    Returns the osc settings, the pitch and its bend (head and tail cents; plays on every key).
    Errors: E_ARG (end before start), E_IO, E_NOT_FOUND (isolate without a pitch), E_SANDBOX_VIOLATION, E_NOT_VERIFIED."""
    opt = options or {}
    target_midi, fade_out_s = float(opt.get("target_midi", -1.0)), float(opt.get("fade_out_s", 0.0))
    chk = call("check_sandbox_path", path=out_path, sandbox_root=str(get_service("sandbox_root")))
    if not chk.ok:
        return chk
    if end_s and end_s <= start_s:
        return fail("E_ARG", "end_s must be after start_s")
    try:
        x, rate = soundbrief.load_slice(path, start_s, end_s)
    except ValueError as e:
        return fail("E_IO", str(e))
    x = np.asarray(x, float) if np.ndim(x) == 2 else np.asarray(x, float)[:, None]
    got = _shape(x, rate, role, opt)
    if isinstance(got, Result):
        return got
    x, f0, extra = got
    n = min(int(FADE_S * rate), len(x) // 4)
    ramp = np.linspace(0.0, 1.0, n)[:, None]
    x = x.copy()
    x[:n] *= ramp
    x[len(x) - n:] *= ramp[::-1]
    if fade_out_s > 0:
        k = min(len(x) - n, int(fade_out_s * rate))
        x[len(x) - k:] *= np.cos(np.linspace(0.0, np.pi / 2, k))[:, None] ** 2
    out = Path(out_path).with_suffix(".wav")
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out), np.clip(x, -1.0, 1.0), rate, subtype="PCM_24")
    plan = wavetables.sampler_plan(x, rate, role, str(out), None if target_midi < 0 else target_midi, f0 or 0.0)
    info = sf.info(str(out))
    if info.frames != len(x) or info.samplerate != rate:
        return fail("E_NOT_VERIFIED", "the cut does not read back at its length", path=str(out))
    return ok({"path": str(out), **plan, **extra}, verified=True)
