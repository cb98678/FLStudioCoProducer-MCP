from __future__ import annotations

from coproducer import call
from coproducer.result import Result, ok


def setup_sidechain_route(source: int, dest: int) -> Result:
    """Create the send from mixer track source to track dest (verified through the API), then make it a sidechain send in the mixer.

    The compressor's own source selector is a separate step (set_sidechain_source_gui). Errors: whatever the route or the GUI step reports.
    """
    route = call("create_send_route", source_index=source, bus_index=dest)
    if not route.ok:
        return route
    flag = call("set_sidechain_send_gui", source=source, dest=dest)
    if not flag.ok:
        return flag
    return ok({"source": source, "dest": dest, "route": route.value}, verified=False, note="the sidechain flag is GUI only and not readable through the API")
