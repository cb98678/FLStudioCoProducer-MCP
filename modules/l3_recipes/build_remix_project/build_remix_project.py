from __future__ import annotations

from pathlib import Path

from coproducer import call, remixbuild, songplan
from coproducer.result import Result, fail, ok
from coproducer.services import get_service

OPTIONS = ("serum_project", "serum_presets", "serum_db", "serum_states", "kit", "solo", "stab_offbeat", "organize", "demo_dir", "record_variety")


def build_remix_project(base_project: str, sytrus_project: str, audio_dir: str, out_project: str, plan_file: str = "", options: dict | None = None) -> Result:
    """Build the remix project (editable patterns for drums, bass, stabs and chops; playlist clips for vocal and FX bed) from a song plan, as a sandbox copy.

    plan_file: plans/NAME.json (default: the plan loaded in remixplan). options: serum_project, serum_presets, serum_db, serum_states, kit,
    solo, stab_offbeat, organize (default true), demo_dir (the demos' render copies for a plan's instruments, default sandbox/demo_study/render),
    record_variety (default true: the plan's choices go into sandbox/variety_history.json). See docs/STEM_REMIX_PIPELINE.md. Errors:
    E_SANDBOX_VIOLATION, E_NOT_FOUND, E_ARG (bad plan or option), E_IO."""
    opt = options or {}
    bad = [k for k in opt if k not in OPTIONS]
    if bad:
        return fail("E_ARG", "unknown options: %s" % ", ".join(bad))
    chk = call("check_sandbox_path", path=out_project, sandbox_root=str(get_service("sandbox_root")))
    if not chk.ok:
        return chk
    try:
        plan = songplan.load(plan_file) if plan_file else None
        if plan is not None:
            songplan.apply(plan)
        root = Path(get_service("sandbox_root"))
        demo_dir = opt.get("demo_dir") or str(root / "demo_study" / "render")
        rep = remixbuild.build(base_project, sytrus_project, audio_dir, out_project, serum=opt.get("serum_project", ""), serum_preset=opt.get("serum_presets"),
                               serum_db=opt.get("serum_db"), serum_state=opt.get("serum_states"), kit=opt.get("kit"), stab_offbeat=bool(opt.get("stab_offbeat")), solo=opt.get("solo", ""), organize=opt.get("organize", True) is not False,
                               demo_dir=demo_dir, log=lambda *a: None)
        if plan is not None and plan.get("variety") and opt.get("record_variety", True) is not False:
            rep["variety_history"] = _record(root, plan)
    except (remixbuild.BuildError, songplan.PlanError) as e:
        return fail("E_ARG", str(e))
    except (OSError, ValueError, KeyError) as e:
        return fail("E_IO" if isinstance(e, OSError) else "E_NOT_FOUND", str(e))
    return ok(rep, verified=rep["channels"] > 0 and rep["patterns"] > 0)


def _record(root, plan: dict) -> int:
    """Add the plan's variety choices to the sandbox's remix history; returns how many remixes it holds."""
    from coproducer import variety
    return variety.record(root / "variety_history.json", plan["name"], plan["variety"])
