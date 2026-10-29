from __future__ import annotations

import numpy as np

from coproducer import dsp, vocalchops
from coproducer.result import Result, fail, ok


def check_vocal_edges(path: str, fade_ms: float = 35.0) -> Result:
    """Judge the end of a finished vocal chop (cut mid-sound?), report its start level, and say whether it ends on a hiss (the s of "blues", "places").

    Levels are read just inside the fades, relative to the loudest 10 ms. An end louder than -18 dB with no hiss on it was cut while the sound was still going.
    ends_on_hiss: the last 100 ms hold a 4 to 12 kHz burst within 16 dB of the total level. Any hiss counts, so the middle s of "places" passes too; use
    find_final_s_end on the stem for the last one. The start level is reported, not judged: only the ear or the recogniser can hear a leftover syllable.
    """
    try:
        x, rate = dsp.load_audio(path)
    except ValueError as e:
        return fail("E_IO", str(e))
    mono = x.mean(axis=1)
    if len(mono) < int(0.15 * rate):
        return fail("E_ARG", "the chop is shorter than 150 ms")
    env, w = vocalchops.envelope_db(mono, rate, 0.01)
    hf = vocalchops.hf_db(mono, rate, 0.01)[: len(env)]
    peak = float(env.max())
    n_fade = int(round(fade_ms / 10.0))
    start_i = 2  # past the 5 ms fade in
    end_i = len(env) - 1 - n_fade  # just inside the fade out
    start_rel, end_rel = float(env[start_i] - peak), float(env[max(end_i, start_i)] - peak)
    tail = slice(max(0, len(env) - 10), len(env))
    tail_hf = float(hf[tail].max() - peak)
    dominant = bool(np.any(hf[tail] > env[tail] - 16.0))
    hissy = bool(tail_hf > -38.0 and dominant)
    return ok({"start_rel_db": round(start_rel, 1), "end_rel_db": round(end_rel, 1), "abrupt_end": bool(end_rel > -18.0 and not hissy),
               "ends_on_hiss": hissy, "tail_hf_rel_db": round(tail_hf, 1), "length_s": round(len(mono) / rate, 3)})
