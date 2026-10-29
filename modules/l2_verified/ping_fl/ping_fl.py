from __future__ import annotations

from coproducer import call
from coproducer.result import Result, first_error, ok


def ping_fl() -> Result:
    """Return FL Studio's version, scripting API level and the active project name.

    Errors: any bridge or FL error from the three reads.
    """
    api = call("op_general_get_version")
    fl = call("op_ui_get_version")
    title = call("op_ui_get_prog_title")
    bad = first_error(api, fl, title)
    if bad:
        return bad
    return ok({"api": api.value, "fl": fl.value, "project": title.value})
