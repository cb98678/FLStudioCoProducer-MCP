from __future__ import annotations

from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def check_gpu_budget(model: str = "") -> Result:
    """Report free and total GPU memory and the loaded models. With a model name, say whether it fits and what would be unloaded.

    free_mb is null when no NVIDIA GPU can be queried.
    """
    sched = get_service("scheduler")
    if sched is None:
        return fail("E_UNSUPPORTED_API", "no model scheduler is configured; run coproducer setup")
    status = sched.status()
    if not model:
        return ok(status)
    spec = sched.registry.get(model)
    if spec is None:
        return fail("E_NOT_FOUND", "no model named %r" % model, nearest=sorted(sched.registry))
    free, gone = status["free_mb"], []
    for name in sched._evict_order():
        if free is None or free >= spec.vram_typical_mb:
            break
        free += status["resident"][name]["need_mb"]
        gone.append(name)
    return ok({**status, "model": model, "need_mb": spec.vram_typical_mb, "fits_now": not gone, "would_unload": gone})
