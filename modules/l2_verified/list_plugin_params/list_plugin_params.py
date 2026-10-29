from __future__ import annotations

from coproducer import call
from coproducer.result import Result, ok


def list_plugin_params(index: int, slot_index: int = -1, offset: int = 0, limit: int = 256) -> Result:
    """List one page of a plugin's non-empty parameter names with their indexes.

    index is the channel (slot -1) or mixer track; slot_index is the effect slot. Use next to fetch more.
    """
    count = call("op_plugins_get_param_count", index=index, slotIndex=slot_index)
    if not count.ok:
        return count
    stop = min(count.value, offset + limit)
    params = []
    for i in range(offset, stop):
        name = call("op_plugins_get_param_name", paramIndex=i, index=index, slotIndex=slot_index)
        if not name.ok:
            return name
        if name.value:
            params.append({"param": i, "name": name.value})
    return ok({"count": count.value, "offset": offset, "params": params, "next": stop if stop < count.value else None})
