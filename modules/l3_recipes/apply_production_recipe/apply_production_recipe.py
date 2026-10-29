from __future__ import annotations

from coproducer import call, flpfile, production, songplan, variety
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def apply_production_recipe(project: str, out_project: str, recipe: str = "club_house", key: str = "A", dry_run: bool = False, plan_file: str = "") -> Result:
    """Apply a whole production recipe (recipes/production/NAME.json) to an arrangement in one step, in a sandbox copy of an FL-saved project
    with time markers and role-named parts: buses and routing, effect chains by role, the pump, transitions at every section change by the kinds
    of the two sections, risers and impacts, section gains and the house standard. Returns every step with ok or the reason it did not apply.
    dry_run reports without writing; plan_file merges that song plan's production_overrides (its variety choices) into the recipe. Render and
    measure after (measure_section_levels, measure_pump_depth). Errors: E_SANDBOX_VIOLATION, E_ARG, E_IO."""
    chk = call("check_sandbox_path", path=out_project, sandbox_root=str(get_service("sandbox_root")))
    if not chk.ok:
        return chk
    try:
        f = flpfile.Flp.load(project)
        rec = production.load_recipe(recipe)
        if plan_file:
            rec = variety.merge_recipe(rec, songplan.load(plan_file).get("production_overrides") or {})
        log = production.apply(f, rec, key, tuple(get_service("fl_not_owned") or ()))
        done = [s for s in log if s["ok"]]
        if not done:
            return fail("E_ARG", "no step applied: %s" % [s.get("why") for s in log][:5])
        if not dry_run:
            f.save(out_project)
            flpfile.Flp.load(out_project)
    except flpfile.FlpError as e:
        return fail("E_ARG", str(e))
    except OSError as e:
        return fail("E_IO", str(e))
    return ok({"out_project": None if dry_run else out_project, "applied": len(done), "not_applied": [s for s in log if not s["ok"]],
               "steps": [{"step": s["step"], "ok": s["ok"]} for s in log]}, verified=None if dry_run else True)
