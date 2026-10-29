from __future__ import annotations

from coproducer.result import Result, fail
from coproducer.services import get_service


def unload_model(model: str) -> Result:
    """Stop a model's runner and free its GPU memory. Unloading a model that is not loaded is not an error."""
    sched = get_service("scheduler")
    if sched is None:
        return fail("E_UNSUPPORTED_API", "no model scheduler is configured; run coproducer setup")
    return sched.unload(model)
