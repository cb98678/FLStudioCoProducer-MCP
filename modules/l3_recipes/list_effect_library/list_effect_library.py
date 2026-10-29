from __future__ import annotations

from coproducer import fxlib
from coproducer.result import Result, ok


def list_effect_library(plugin: str = "", text: str = "", with_params: bool = False) -> Result:
    """List the effect library: saved effect settings that apply_effect_from_library can put into a mixer slot. Filter by plugin name and by any
    text in the entry name or notes; with_params adds each entry's parameter texts as read in FL when it was saved."""
    rows = []
    for e in fxlib.list_entries():
        if plugin and plugin.lower() not in e["plugin"].lower():
            continue
        if text and text.lower() not in (e["name"] + " " + e["notes"]).lower():
            continue
        if with_params:
            e = dict(e, params=fxlib.load_entry(e["name"]).get("params", {}))
        rows.append(e)
    return ok({"count": len(rows), "entries": rows})
