from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def set_tempo_verified(bpm: float) -> Result:
    """Set the project tempo in beats per minute and confirm by reading it back.

    Measured on FL 26.1.7: the setter takes whole milli-BPM (128000 is 128 BPM) and raises a range error for
    anything else, and getCurrentTempo(True) returns BPM as a float. Errors: E_ARG when FL rejects the value,
    E_NOT_VERIFIED when the readback differs.
    """
    milli = int(round(bpm * 1000))
    w = call("op_mixer_set_current_tempo", tempo=milli)
    if not w.ok:
        return w
    r = call("op_mixer_get_current_tempo", asInt=True)
    if not r.ok:
        return r
    if abs(r.value - milli / 1000.0) > 0.01:
        return fail("E_NOT_VERIFIED", "wrote %r bpm but read back %r" % (bpm, r.value), wrote=bpm, read=r.value)
    return ok(r.value, verified=True)
