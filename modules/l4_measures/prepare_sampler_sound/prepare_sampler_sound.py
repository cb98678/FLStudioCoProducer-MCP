from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

from coproducer import call, soundbrief, wavetables
from coproducer.result import Result, fail, ok
from coproducer.services import get_service

FADE_S = 0.003


def prepare_sampler_sound(path: str, out_path: str, role: str, start_s: float = 0.0, end_s: float = 0.0, target_midi: float = -1.0) -> Result:
    """Cut path (start_s to end_s, the whole file by default) into out_path, a 24-bit WAV in the sandbox with 3 ms fades, for serum-mcp's
    sample_playback_source (WAV only). Returns the osc settings: the file plays at its own pitch and speed on note 60 (FL's C5); a bass
    or melodic sound is transposed so each note plays as itself (or note 60 as target_midi), with a sustain loop; a vocal or a drum is not.
    Errors: E_ARG (end before start), E_IO, E_SANDBOX_VIOLATION, E_NOT_VERIFIED."""
    chk = call("check_sandbox_path", path=out_path, sandbox_root=str(get_service("sandbox_root")))
    if not chk.ok:
        return chk
    if end_s and end_s <= start_s:
        return fail("E_ARG", "end_s must be after start_s")
    try:
        x, rate = soundbrief.load_slice(path, start_s, end_s)
    except ValueError as e:
        return fail("E_IO", str(e))
    n = min(int(FADE_S * rate), len(x) // 4)
    ramp = np.linspace(0.0, 1.0, n)[:, None]
    x = x.copy()
    x[:n] *= ramp
    x[len(x) - n:] *= ramp[::-1]
    out = Path(out_path).with_suffix(".wav")
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out), np.clip(x, -1.0, 1.0), rate, subtype="PCM_24")
    plan = wavetables.sampler_plan(x, rate, role, str(out), None if target_midi < 0 else target_midi)
    info = sf.info(str(out))
    if info.frames != len(x) or info.samplerate != rate:
        return fail("E_NOT_VERIFIED", "the cut does not read back at its length", path=str(out))
    return ok({"path": str(out), **plan}, verified=True)
