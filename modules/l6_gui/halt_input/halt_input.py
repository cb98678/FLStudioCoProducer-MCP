from __future__ import annotations

from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def halt_input() -> Result:
    """Set the halt flag: every input primitive refuses to act until a human clears it. Safe to call at any time."""
    halt = get_service("halt")
    if halt is None:
        return fail("E_UNSUPPORTED_API", "no halt flag is configured")
    halt.set()
    return ok({"halted": True})
