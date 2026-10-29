from __future__ import annotations

from coproducer import call
from coproducer.result import Result, first_error, ok


def restore_after_render(was_playing: bool, position: float, loop_song: bool) -> Result:
    """Put loop mode, song position and play state back to what prepare_for_render recorded.

    Errors: the first verified step that fails.
    """
    loop = call("ensure_loop_mode", song=loop_song)
    pos = call("set_song_position_verified", position=position)
    bad = first_error(loop, pos)
    if bad:
        return bad
    play = call("ensure_playing") if was_playing else call("ensure_stopped")
    if not play.ok:
        return play
    return ok({"position": pos.value, "loop_song": loop_song, "playing": was_playing}, verified=True)
