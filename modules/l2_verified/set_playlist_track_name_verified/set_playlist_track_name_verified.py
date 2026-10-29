from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def set_playlist_track_name_verified(index: int, name: str) -> Result:
    """Rename a playlist track and confirm by reading the name back.

    Errors: E_ARG for bad input or an FL-side failure, E_NOT_VERIFIED when the readback differs.
    """
    w = call("op_playlist_set_track_name", index=index, name=name)
    if not w.ok:
        return w
    r = call("op_playlist_get_track_name", index=index)
    if not r.ok:
        return r
    if r.value != name:
        return fail("E_NOT_VERIFIED", "wrote %r but read back %r" % (name, r.value), wrote=name, read=r.value)
    return ok(r.value, verified=True)
