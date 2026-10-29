from __future__ import annotations

from coproducer import call, flpfile, projorg
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def apply_project_standard(project: str, out_project: str, dry_run: bool = False, drop_unused: bool = False) -> Result:
    """Name, colour and group a project the house way (docs/PROJECT_STANDARD.md): channels, mixer inserts, patterns and playlist rows by family
    (drums green, bass orange, synths purple, vocals blue, FX red). Writes a new project under the sandbox folder; the source is only read.
    No fader, routing or plugin changes. dry_run returns the plan and writes nothing. Channels that play nothing (no notes, no playlist clip) are always
    listed as unused_channels; drop_unused removes only the ones routed to no mixer insert from the copy."""
    chk = call("check_sandbox_path", path=out_project, sandbox_root=str(get_service("sandbox_root")))
    if not chk.ok:
        return chk
    try:
        f = flpfile.Flp.load(project)
        if dry_run:
            return ok({"plan": projorg.plan(f), "problems": projorg.check(f), "unused_channels": projorg.unused_channels(f)}, verified=True)
        unused = projorg.drop_unused(f) if drop_unused else projorg.unused_channels(f)
        plan = projorg.plan(f)
        counts = projorg.apply(f, plan)
        f.save(out_project)
        left = projorg.check(flpfile.Flp.load(out_project))
    except (OSError, flpfile.FlpError) as e:
        return fail("E_IO", str(e))
    unclassified = [r["old"] for r in plan["channels"] if not r["family"]]
    return ok({"changed": counts, "out_project": out_project, "left": left, "unclassified_channels": unclassified,
                "unused_channels": [u["name"] for u in projorg.unused_channels(flpfile.Flp.load(project))], "dropped": [u["name"] for u in unused] if drop_unused else []}, verified=not left)
