from __future__ import annotations

from coproducer import flpfile, projorg
from coproducer.result import Result, fail, ok

FAMILIES = ("drums", "bass", "synths", "vocals", "fx")


def list_family_inserts(project: str, families: list[str] | None = None) -> Result:
    """List the mixer inserts of a saved project by family (drums, bass, synths, vocals, fx): insert number, its name in the file, the family colour. Also
    returns first_free, the first insert after the last used one. The project is only read. Errors: E_ARG for an unknown family or none found, E_IO."""
    want = list(families or FAMILIES)
    bad = [x for x in want if x not in FAMILIES]
    if bad:
        return fail("E_ARG", "unknown families: %s" % ", ".join(bad))
    try:
        rows = projorg.plan_tracks(flpfile.Flp.load(project))
    except (OSError, flpfile.FlpError) as e:
        return fail("E_IO", str(e))
    mine = [{"track": r["track"], "name": r["old"] or "Insert %d" % r["track"], "family": r["family"], "rgb": list(r["color"])}
            for r in rows if r["family"] in want]
    if not mine:
        return fail("E_ARG", "no inserts of those families in %s" % project)
    return ok({"inserts": mine, "first_free": max(r["track"] for r in rows) + 1, "bus_rgb": list(projorg.PALETTE["bus"]),
               "bus_names": {x: "%s Bus" % projorg.GROUP[x] for x in FAMILIES}}, verified=True)
