from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def set_plugin_param_by_name(index: int, name: str, value: float, slot_index: int = -1) -> Result:
    """Set one plugin parameter (0.0 to 1.0) by name and confirm by reading it back.

    Some plugins round values, so the readback may differ slightly; a gap above 0.005 fails verification.
    """
    pm = call("build_param_map", index=index, slot_index=slot_index)
    if not pm.ok:
        return pm
    if name not in pm.value["map"]:
        return fail("E_NOT_FOUND", "no unique parameter %r on %r" % (name, pm.value["plugin"]),
                    known=sorted(pm.value["map"]), duplicates=sorted(pm.value["duplicates"]))
    p = pm.value["map"][name]
    w = call("op_plugins_set_param_value", value=value, paramIndex=p, index=index, slotIndex=slot_index)
    if not w.ok:
        return w
    r = call("op_plugins_get_param_value", paramIndex=p, index=index, slotIndex=slot_index)
    if not r.ok:
        return r
    if abs(r.value - value) > 0.005:
        return fail("E_NOT_VERIFIED", "wrote %r but read back %r" % (value, r.value), wrote=value, read=r.value)
    return ok(r.value, verified=True, param=p)
