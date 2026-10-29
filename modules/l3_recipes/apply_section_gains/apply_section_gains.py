from __future__ import annotations

from coproducer import call, flpfile, fxlib, pump, sectiongain
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def apply_section_gains(project: str, out_project: str, gains: list | None = None, sections: list | None = None, by_role: dict | None = None, row: int = 0) -> Result:
    """Shape level section by section before the master, as the Future House reference does: each insert gets a Fruity Balance in its last
    free slot (the master: its first, before a limiter) and one automation clip that holds the gain set for each section (0 dB elsewhere, short ramps at the boundaries). gains:
    [{"insert", "sections": {section name: dB}, "label"}], or by_role {kind: {role or "master": dB}} ({} for the default map, {"scale": x} for
    it scaled: turn x until measure_section_levels' contrast meets the target);
    sections: [{"name", "start_bar", "end_bar"}] (bars from 1), default the time markers. Writes a sandbox copy. Errors: E_SANDBOX_VIOLATION, E_ARG, E_IO."""
    chk = call("check_sandbox_path", path=out_project, sandbox_root=str(get_service("sandbox_root")))
    if not chk.ok:
        return chk
    if not gains and by_role is None:
        return fail("E_ARG", "give gains per insert, or by_role")
    try:
        f = flpfile.Flp.load(project)
        secs = sections or sectiongain.sections_from_markers(f)
        role_map = sectiongain.DEFAULT_ROLE_GAINS
        if by_role and set(by_role) != {"scale"}:
            role_map = by_role
        elif by_role:
            role_map = sectiongain.scaled(role_map, float(by_role["scale"]))
        gains = gains or sectiongain.gains_by_role(f, secs, role_map)
        if not gains:
            return fail("E_ARG", "no insert has a role and no section a kind in the map")
        lane = row or pump.first_free_row(f)
        done = [sectiongain.apply_gains(f, int(g["insert"]), g["sections"], secs, lane + k, g.get("label", "")) for k, g in enumerate(gains)]
        f.save(out_project)
        g2 = flpfile.Flp.load(out_project)
        back = all(d["clip"] in g2.channel_ids() and fxlib.slot_plugin(g2, d["insert"], d["slot"]) == "Fruity Balance" for d in done)
    except (flpfile.FlpError, KeyError, TypeError) as e:
        return fail("E_ARG", str(e))
    except OSError as e:
        return fail("E_IO", str(e))
    return ok({"out_project": out_project, "sections": secs, "placed": done}, verified=back)
