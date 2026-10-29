from __future__ import annotations

from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def send_request(frames: list[list[int]]) -> Result:
    """Send each framed message on the bridge transport, in order.

    Errors: E_UNSUPPORTED_API without a transport, E_IO when sending fails.
    """
    transport = get_service("transport")
    if transport is None:
        return fail("E_UNSUPPORTED_API", "no bridge transport is configured")
    sent = 0
    for frame in frames:
        try:
            transport.send(bytes(frame))
        except Exception as e:  # noqa: BLE001
            return fail("E_IO", f"send failed after {sent} frames: {e}", retryable=False, sent=sent)
        sent += 1
    return ok({"sent": sent})
