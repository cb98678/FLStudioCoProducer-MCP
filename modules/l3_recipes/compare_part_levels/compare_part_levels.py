from __future__ import annotations

from coproducer import call, flpfile, partmix
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def compare_part_levels(project: str, solo_dir: str, render_dir: str, profile: dict, out_project: str = "") -> Result:
    """Compare each part's solo loudness with `profile` (from measure_part_levels on an approved mix) and return the fader changes, at most 12 dB a pass; the kick
    and master never move. With out_project (inside the sandbox) the changes are written into that copy and read back. Render again and re-run to confirm."""
    if out_project:
        chk = call("check_sandbox_path", path=out_project, sandbox_root=str(get_service("sandbox_root")))
        if not chk.ok:
            return chk
    try:
        f = flpfile.Flp.load(project)
        _man, levels, roles, missing = partmix.measure_dir(solo_dir, render_dir)
        changes = partmix.plan_changes(levels, roles, partmix.faders_db(f, list(levels)), profile)
        if out_project:
            partmix.apply_changes(f, changes)
            f.save(out_project)
    except (OSError, ValueError, KeyError, flpfile.FlpError) as e:
        return fail("E_IO", str(e))
    verified = True
    if out_project and changes:
        g = flpfile.Flp.load(out_project)
        verified = all(abs(partmix.faders_db(g, [c["track"]])[c["track"]] - c["new_db"]) <= 0.6 for c in changes)
    return ok({"changes": changes, "missing": missing, "within_tolerance": not changes, "written": out_project or None}, verified=verified)
