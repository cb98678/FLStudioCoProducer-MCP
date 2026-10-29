from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok

BUS_FAMILIES = ["drums", "vocals", "fx"]


def build_family_buses(project: str, families: list[str] | None = None, level: float | None = None) -> Result:
    """Build one yellow bus insert per family (default drums, vocals, fx) in the project open in FL and send that family's inserts through it, the bus to the
    master. `project` is the saved .flp that is open: it says which inserts belong to which family, and the open project is checked against it first. Buses take
    the first free inserts after the last used one and are named like Drums Bus. level defaults to what each insert sends to the master now, so the mix does not change. Every step is read back; run it again and it reuses the
    same inserts. Errors: E_ARG when the open project differs or an insert is not free, E_NOT_VERIFIED."""
    listed = call("list_family_inserts", project=project, families=families or BUS_FAMILIES)
    if not listed.ok:
        return listed
    v = listed.value
    same = call("check_open_project", inserts=v["inserts"])
    if not same.ok:
        return same
    out = []
    for slot, fam in enumerate(dict.fromkeys(i["family"] for i in v["inserts"]), start=v["first_free"]):
        name = v["bus_names"][fam]
        cur = call("op_mixer_get_track_name", index=slot)
        if not cur.ok:
            return cur
        if cur.value not in ("Insert %d" % slot, name):
            return fail("E_ARG", "insert %d is not free (it is named %r)" % (slot, cur.value))
        wired = call("route_tracks_through_bus", sources=[i["track"] for i in v["inserts"] if i["family"] == fam], bus_index=slot, name=name, **({} if level is None else {"level": level}))
        if not wired.ok:
            return wired
        for ref in v["inserts"]:  # the colour order comes from an insert FL shows in its family colour
            paint = call("set_track_color_verified", index=slot, rgb=v["bus_rgb"], like_index=ref["track"], like_rgb=ref["rgb"])
            if paint.ok:
                break
        if not paint.ok:
            return paint
        out.append({"family": fam, **wired.value})
    return ok({"buses": out}, verified=True)
