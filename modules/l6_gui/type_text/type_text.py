from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def type_text(text: str, interval_s: float = 0.02) -> Result:
    """Type text into whatever FL Studio control has the focus. Printable characters only, at most 300.

    Errors: E_ARG for control characters, plus every refusal of check_desktop_ready.
    """
    if any(ord(c) < 32 or ord(c) == 127 for c in text):
        return fail("E_ARG", "text may not contain control characters; use press_hotkey for keys like Enter")
    ready = call("check_desktop_ready")
    if not ready.ok:
        return ready
    get_service("desktop").type_text(text, interval_s)
    return ok({"typed": len(text)})
