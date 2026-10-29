from __future__ import annotations

from coproducer import call
from coproducer.result import Result, ok


def build_bus(track_indexes: list[int], bus_index: int, name: str, level: float = 0.8) -> Result:
    """Name a mixer track as a bus and send each listed track to it at the given level, all verified.

    Errors: the first failing step.
    """
    named = call("set_track_name_verified", index=bus_index, name=name)
    if not named.ok:
        return named
    routes = []
    for i in track_indexes:
        r = call("create_send_route", source_index=i, bus_index=bus_index, level=level)
        if not r.ok:
            return r
        routes.append(r.value)
    return ok({"bus": bus_index, "name": named.value, "routes": routes}, verified=True)
