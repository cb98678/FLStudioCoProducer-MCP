from __future__ import annotations

import time

from coproducer import call
from coproducer.result import Result, fail, ok


def ensure_playing(wait_s: float = 1.0) -> Result:
    """Make the transport play if it is not already playing, and confirm.

    Start toggles play and pause, so the state is read first. Errors: E_NOT_VERIFIED if it never starts.
    """
    cur = call("op_transport_is_playing")
    if not cur.ok or cur.value:
        return cur if not cur.ok else ok(True, verified=True, changed=False)
    w = call("op_transport_start")
    if not w.ok:
        return w
    deadline = time.monotonic() + wait_s
    while True:
        r = call("op_transport_is_playing")
        if not r.ok or r.value:
            return r if not r.ok else ok(True, verified=True, changed=True)
        if time.monotonic() >= deadline:
            return fail("E_NOT_VERIFIED", "transport did not start within %.1fs" % wait_s)
        time.sleep(0.05)
