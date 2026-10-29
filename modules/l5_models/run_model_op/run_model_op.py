from __future__ import annotations

from coproducer.result import Result, fail
from coproducer.services import get_service


def run_model_op(model: str, op: str, args: dict, timeout_s: float = 600.0) -> Result:
    """Run one operation on a local model through the GPU scheduler, loading it first if needed.

    Errors: E_UNSUPPORTED_API without a scheduler, E_GPU_BUDGET, E_MODEL, E_TIMEOUT (the runner is stopped).
    """
    sched = get_service("scheduler")
    if sched is None:
        return fail("E_UNSUPPORTED_API", "no model scheduler is configured; run coproducer setup")
    return sched.run_op(model, op, args, timeout_s)
