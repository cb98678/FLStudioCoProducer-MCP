from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def _current_level(src: int, bus_index: int) -> Result:
    """What the source sends now: to the master, or (on a rerun, after it was moved) to the bus."""
    was = call("op_mixer_get_route_to_level", index=src, destIndex=0)
    return was if was.ok else call("op_mixer_get_route_to_level", index=src, destIndex=bus_index)


def route_tracks_through_bus(sources: list[int], bus_index: int, name: str, level: float | None = None) -> Result:
    """Name a mixer track as a bus, send each source track to it at `level` (default: the level that source now sends to the master, so the mix does not change), turn each source's direct route to
    the master off and make sure the bus reaches the master. Every step is read back. Errors: the first failing step, E_NOT_VERIFIED."""
    named = call("set_track_name_verified", index=bus_index, name=name)
    if not named.ok:
        return named
    routes = []
    for src in sources:
        was = _current_level(src, bus_index)
        if not was.ok:
            return was
        sent = call("create_send_route", source_index=src, bus_index=bus_index, level=was.value if level is None else level)
        if not sent.ok:
            return sent
        for step in (call("op_mixer_set_route_to", index=src, destIndex=0, value=False), call("op_mixer_get_route_send_active", index=src, destIndex=0)):
            if not step.ok:
                return step
        if step.value:
            return fail("E_NOT_VERIFIED", "track %d still sends to the master" % src)
        routes.append(sent.value)
    for step in (call("op_mixer_set_route_to", index=bus_index, destIndex=0, value=True), call("op_mixer_get_route_send_active", index=bus_index, destIndex=0)):
        if not step.ok:
            return step
    if not step.value:
        return fail("E_NOT_VERIFIED", "%s does not send to the master" % name)
    return ok({"bus": bus_index, "name": name, "sources": sources, "routes": routes}, verified=True)
