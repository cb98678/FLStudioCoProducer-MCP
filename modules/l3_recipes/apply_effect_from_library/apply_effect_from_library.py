from __future__ import annotations

from coproducer import call, flpfile, fxlib
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def apply_effect_from_library(project: str, out_project: str, placements: list) -> Result:
    """Put effects from the effect library (list_effect_library) into empty mixer slots, with every setting the entry holds, and write a new project
    under the sandbox folder; the source is only read. placements: [{"insert", "slot", "name"}]. The source must be a project FL itself saved.
    Refuses a slot that already holds an effect. FL is the proof: open the copy, then read the slot back with get_plugin_param_by_name or
    snapshot_project_params and compare with the entry's params. Errors: E_SANDBOX_VIOLATION, E_ARG, E_IO."""
    chk = call("check_sandbox_path", path=out_project, sandbox_root=str(get_service("sandbox_root")))
    if not chk.ok:
        return chk
    if not placements:
        return fail("E_ARG", "give at least one placement")
    try:
        f = flpfile.Flp.load(project)
        done = []
        for p in placements:
            entry = fxlib.load_entry(p["name"])
            fxlib.inject(f, int(p["insert"]), int(p["slot"]), entry)
            done.append({"insert": p["insert"], "slot": p["slot"], "name": entry["name"], "plugin": entry["plugin"], "expect": entry.get("params", {})})
        f.save(out_project)
        back = flpfile.Flp.load(out_project)
        placed = [fxlib.slot_plugin(back, d["insert"], d["slot"]) == d["plugin"] for d in done]
    except flpfile.FlpError as e:
        return fail("E_ARG", str(e))
    except OSError as e:
        return fail("E_IO", str(e))
    return ok({"out_project": out_project, "placed": done}, verified=all(placed))
