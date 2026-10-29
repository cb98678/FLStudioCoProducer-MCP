from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def check_open_project(inserts: list[dict]) -> Result:
    """Confirm the project open in FL is the one a file listing came from: every listed insert must carry the same name in FL (an unnamed insert reads
    Insert N). Stops writing modules from changing the wrong project. Errors: E_ARG naming the first insert that differs."""
    for r in inserts:
        live = call("op_mixer_get_track_name", index=r["track"])
        if not live.ok:
            return live
        if live.value != r["name"]:
            return fail("E_ARG", "the open project is not the saved one: insert %d is %r in FL and %r in the file" % (r["track"], live.value, r["name"]))
    return ok({"checked": len(inserts)}, verified=True)
