from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def set_song_position_verified(position: float) -> Result:
    """Set the song position and confirm by reading it back.

    Units follow FL's default position mode; Gate 0 records what that is on your build.
    """
    w = call("op_transport_set_song_pos", position=position)
    if not w.ok:
        return w
    r = call("op_transport_get_song_pos")
    if not r.ok:
        return r
    if abs(r.value - position) > max(0.001, abs(position) * 1e-4):
        return fail("E_NOT_VERIFIED", "wrote %r but read back %r" % (position, r.value), wrote=position, read=r.value)
    return ok(r.value, verified=True)
