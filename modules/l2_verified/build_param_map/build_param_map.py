from __future__ import annotations

from coproducer import call
from coproducer.result import Result, ok
from coproducer.services import get_service, set_service


def build_param_map(index: int, slot_index: int = -1, refresh: bool = False) -> Result:
    """Build a name to parameter-index map for one plugin and cache it for the session.

    Names that occur more than once are listed under duplicates and are not placed in the map.
    """
    name = call("op_plugins_get_plugin_name", index=index, slotIndex=slot_index)
    if not name.ok:
        return name
    key = "%d:%d:%s" % (index, slot_index, name.value)
    cache = get_service("param_maps", {})
    if key in cache and not refresh:
        return ok(cache[key], cached=True)
    page = call("list_plugin_params", index=index, slot_index=slot_index, limit=4096)
    if not page.ok:
        return page
    seen: dict = {}
    for p in page.value["params"]:
        seen.setdefault(p["name"], []).append(p["param"])
    result = {"plugin": name.value, "map": {n: v[0] for n, v in seen.items() if len(v) == 1},
              "duplicates": {n: v for n, v in seen.items() if len(v) > 1}}
    cache[key] = result
    set_service("param_maps", cache)
    return ok(result, cached=False)
