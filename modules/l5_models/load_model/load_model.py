from __future__ import annotations

from coproducer.result import Result, fail
from coproducer.services import get_service


def load_model(model: str, variant: str = "") -> Result:
    """Start a registered model through the scheduler, unloading others if memory is short.

    Errors: E_NOT_FOUND unknown model, E_GPU_BUDGET will not fit, E_MODEL the environment or runner is missing.
    """
    sched = get_service("scheduler")
    if sched is None:
        return fail("E_UNSUPPORTED_API", "no model scheduler is configured; run coproducer setup")
    return sched.load(model, variant or None)
