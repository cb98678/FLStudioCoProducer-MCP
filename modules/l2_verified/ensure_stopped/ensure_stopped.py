from __future__ import annotations

import time

from coproducer import call
from coproducer.result import Result, fail, ok


def ensure_stopped(wait_s: float = 1.0) -> Result:
    """Make the transport stop if it is playing, and confirm.

    Errors: E_NOT_VERIFIED if it is still playing after wait_s seconds.
    """
    cur = call("op_transport_is_playing")
    if not cur.ok or not cur.value:
        return cur if not cur.ok else ok(True, verified=True, changed=False)
    w = call("op_transport_stop")
    if not w.ok:
        return w
    deadline = time.monotonic() + wait_s
    while True:
        r = call("op_transport_is_playing")
        if not r.ok or not r.value:
            return r if not r.ok else ok(True, verified=True, changed=True)
        if time.monotonic() >= deadline:
            return fail("E_NOT_VERIFIED", "transport did not stop within %.1fs" % wait_s)
        time.sleep(0.05)
