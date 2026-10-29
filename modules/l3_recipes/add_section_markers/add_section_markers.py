from __future__ import annotations

from coproducer import call, flpfile
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def add_section_markers(project: str, out_project: str, sections: list) -> Result:
    """Write time markers for song sections into the current arrangement of a sandbox copy, the way FL 26 writes them, so FL shows the sections and
    section-aware tools (measure_section_levels, add_transition_automation) can find them. sections: [{"name", "bar"}], bar 1 is the start.
    The source is only read. Errors: E_SANDBOX_VIOLATION, E_ARG, E_IO."""
    chk = call("check_sandbox_path", path=out_project, sandbox_root=str(get_service("sandbox_root")))
    if not chk.ok:
        return chk
    if not sections:
        return fail("E_ARG", "give at least one section")
    try:
        f = flpfile.Flp.load(project)
        for s in sections:
            f.add_time_marker(int(round((float(s["bar"]) - 1) * flpfile.TICKS_PER_BAR)), str(s["name"]))
        f.save(out_project)
        back = [m["name"] for m in flpfile.Flp.load(out_project).time_markers()]
    except flpfile.FlpError as e:
        return fail("E_ARG", str(e))
    except OSError as e:
        return fail("E_IO", str(e))
    return ok({"out_project": out_project, "markers": back}, verified=all(str(s["name"]) in back for s in sections))
