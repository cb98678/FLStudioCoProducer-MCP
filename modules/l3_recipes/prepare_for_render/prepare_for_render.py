from __future__ import annotations

from coproducer import call
from coproducer.result import Result, first_error, ok


def prepare_for_render() -> Result:
    """Stop the transport and rewind to the start, returning the state needed by restore_after_render.

    The value also reports unsaved changes: FL renders the saved project file, so save first if unsaved is true.
    """
    pos = call("op_transport_get_song_pos")
    loop = call("op_transport_get_loop_mode")
    dirty = call("op_general_get_changed_flag")
    stopped = call("ensure_stopped")
    bad = first_error(pos, loop, dirty, stopped)
    if bad:
        return bad
    home = call("set_song_position_verified", position=0.0)
    if not home.ok:
        return home
    return ok({"was_playing": stopped.meta["changed"], "position": pos.value, "loop_song": bool(loop.value),
               "unsaved": bool(dirty.value)}, verified=True)
