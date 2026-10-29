from __future__ import annotations

import time

from coproducer import call
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def wait_for_reply(req_id: int, timeout_s: float = 2.0) -> Result:
    """Read frames from the bridge transport until the group for req_id is complete or the time runs out.

    Frames that are not ours are ignored. Errors: E_UNSUPPORTED_API without a transport, E_TIMEOUT.
    """
    transport = get_service("transport")
    if transport is None:
        return fail("E_UNSUPPORTED_API", "no bridge transport is configured")
    deadline = time.monotonic() + timeout_s
    parsed = []
    while time.monotonic() < deadline:
        raw = transport.recv(max(0.0, min(0.05, deadline - time.monotonic())))
        if raw is not None:
            p = call("parse_frame", frame=list(raw))
            if p.ok:
                parsed.append(p.value)
            m = call("match_reply", parsed=parsed, req_id=req_id)
            if m.ok and m.value["complete"]:
                return ok({"type": m.value["type"], "payload": m.value["payload"]})
    return fail("E_TIMEOUT", f"no complete reply for request {req_id} in {timeout_s}s", retryable=True, have=len(parsed))
