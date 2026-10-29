from __future__ import annotations

from coproducer import anatomy, flpfile
from coproducer.result import Result, fail, ok


def read_project_anatomy(project: str, include: list | None = None) -> Result:
    """Read a whole FL project from its file, without FL: channels (type, Layer children, plugin, insert, group, pitch), mixer inserts (name, colour,
    level, routes with send levels, effect slots), automation clips and controller links resolved to insert, slot, plugin and parameter, orphan clips,
    and every arrangement (the current one marked) with markers and named rows. Starts with plain summary lines. Files saved by FL older than 21 are
    read but marked unsupported: re-save them in FL 26 first.
    Errors: E_IO when the file cannot be read."""
    try:
        rep = anatomy.read(flpfile.Flp.load(project))
    except (OSError, flpfile.FlpError, ValueError) as e:
        return fail("E_IO", "cannot read %s: %s" % (project, e))
    if include:
        rep = {k: v for k, v in rep.items() if k in include or k == "summary"}
    warn = [] if rep.get("project", {}).get("supported", True) else ["saved by an FL older than 21: levels and routing may be wrong, re-save in FL 26"]
    return ok({**rep, "warnings": warn})
