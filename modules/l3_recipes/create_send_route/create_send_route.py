from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def create_send_route(source_index: int, bus_index: int, level: float = 0.8) -> Result:
    """Route one mixer track to another (for example a bus) and set the send level, verified.

    Errors: E_NOT_VERIFIED when FL does not report the route as active.
    """
    on = call("op_mixer_set_route_to", index=source_index, destIndex=bus_index, value=True)
    if not on.ok:
        return on
    active = call("op_mixer_get_route_send_active", index=source_index, destIndex=bus_index)
    if not active.ok:
        return active
    if not active.value:
        return fail("E_NOT_VERIFIED", "the route %d to %d did not turn on" % (source_index, bus_index))
    lvl = call("set_route_level_verified", index=source_index, dest_index=bus_index, level=level)
    if not lvl.ok:
        return lvl
    return ok({"source": source_index, "bus": bus_index, "level": lvl.value}, verified=True)
