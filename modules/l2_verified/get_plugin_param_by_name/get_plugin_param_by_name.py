from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def get_plugin_param_by_name(index: int, name: str, slot_index: int = -1) -> Result:
    """Read one plugin parameter (0.0 to 1.0) and its display text by parameter name.

    Errors: E_NOT_FOUND when the name is unknown, E_ARG when it is ambiguous.
    """
    pm = call("build_param_map", index=index, slot_index=slot_index)
    if not pm.ok:
        return pm
    if name in pm.value["duplicates"]:
        return fail("E_ARG", "parameter name %r is ambiguous" % name, indexes=pm.value["duplicates"][name])
    if name not in pm.value["map"]:
        return fail("E_NOT_FOUND", "plugin %r has no parameter %r" % (pm.value["plugin"], name),
                    known=sorted(pm.value["map"]))
    p = pm.value["map"][name]
    val = call("op_plugins_get_param_value", paramIndex=p, index=index, slotIndex=slot_index)
    text = call("op_plugins_get_param_value_string", paramIndex=p, index=index, slotIndex=slot_index)
    if not (val.ok and text.ok):
        return val if not val.ok else text
    return ok({"param": p, "value": val.value, "text": text.value})
