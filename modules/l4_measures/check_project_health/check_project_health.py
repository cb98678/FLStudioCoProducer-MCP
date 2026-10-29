from __future__ import annotations

import json
from pathlib import Path

from coproducer import anatomy, flpfile
from coproducer.result import Result, fail, ok


def check_project_health(project: str, params_file: str = "", not_owned: list | None = None) -> Result:
    """List what a producer would fix before mixing or rendering a project: automation clips linked to nothing or not placed, meters and recorders
    left in effect chains, unnamed channels, empty inserts, extra arrangements, files from an FL older than 21, plugins the person's FL edition does
    not have (pass them in not_owned; FL then shows a trial dialog and command-line renders stall), and, with params_file (a JSON snapshot written
    from snapshot_project_params), a master limiter whose ceiling lets the output pass 0 dBFS. Read only.
    Errors: E_IO when the project or the snapshot cannot be read."""
    try:
        rep = anatomy.read(flpfile.Flp.load(project))
        params = json.loads(Path(params_file).read_text(encoding="utf-8")) if params_file else None
    except (OSError, flpfile.FlpError, ValueError) as e:
        return fail("E_IO", "cannot read: %s" % e)
    items = anatomy.health(rep, params, not_owned)
    problems = [x for x in items if x["severity"] == "problem"]
    return ok({"problems": len(problems), "items": items, "render_safe": not any(x["kind"] == "not_owned" for x in items)})
