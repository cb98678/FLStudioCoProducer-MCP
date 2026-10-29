from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def ensure_loop_mode(song: bool) -> Result:
    """Make the transport loop the song (True) or the pattern (False), and confirm.

    FL only offers a toggle, so the mode is read first. Errors: E_NOT_VERIFIED if the mode does not change.
    """
    want = 1 if song else 0
    cur = call("op_transport_get_loop_mode")
    if not cur.ok or cur.value == want:
        return cur if not cur.ok else ok(want, verified=True, changed=False)
    w = call("op_transport_set_loop_mode")
    if not w.ok:
        return w
    r = call("op_transport_get_loop_mode")
    if not r.ok:
        return r
    if r.value != want:
        return fail("E_NOT_VERIFIED", "loop mode is %r, wanted %r" % (r.value, want), read=r.value)
    return ok(r.value, verified=True, changed=True)
