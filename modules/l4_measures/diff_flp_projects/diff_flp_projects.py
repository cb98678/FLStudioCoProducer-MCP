from __future__ import annotations

from coproducer import flpfile, projdiff
from coproducer.result import Result, fail, ok


def diff_flp_projects(before: str, after: str) -> Result:
    """Say what changed between two FL projects: channels added or removed, samples and Serum presets swapped, mixer level changes in dB, note rhythm per
    channel (count and 16th-step histogram) and audio clip changes. Use it on a build and the copy the person hand-fixed, then change the recipe to match."""
    try:
        a, b = flpfile.Flp.load(before), flpfile.Flp.load(after)
    except (OSError, flpfile.FlpError) as e:
        return fail("E_IO", str(e))
    rep = projdiff.diff_projects(a, b)
    lines = projdiff.summarize(rep)
    return ok({"changes": len(lines), "summary": lines, "report": rep})
