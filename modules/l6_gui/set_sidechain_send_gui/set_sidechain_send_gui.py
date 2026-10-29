from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail


def set_sidechain_send_gui(source: int, dest: int) -> Result:
    """Turn the existing send from mixer track source to track dest into a sidechain send (strips 1 to 16, mixer open).

    The route must exist first (create_send_route). Runs the recipe of the same name.
    Errors: E_ARG for the same track, E_GUI_MISMATCH, E_BLOCKED_BY_DIALOG, E_HALTED.
    """
    if source == dest:
        return fail("E_ARG", "a track cannot sidechain to itself")
    return call("run_gui_recipe", name="set_sidechain_send_gui", params={"source": source, "dest": dest})
