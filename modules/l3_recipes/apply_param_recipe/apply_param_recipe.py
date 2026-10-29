from __future__ import annotations

from coproducer import call
from coproducer.result import Result, ok


def apply_param_recipe(index: int, params: dict, slot_index: int = -1) -> Result:
    """Set several plugin parameters by name (values 0.0 to 1.0), each verified by readback.

    Errors: the first parameter that is unknown, ambiguous or does not stick.
    """
    set_to = {}
    for name, value in params.items():
        r = call("set_plugin_param_by_name", index=index, name=name, value=value, slot_index=slot_index)
        if not r.ok:
            return r
        set_to[name] = r.value
    return ok({"set": set_to}, verified=True)
