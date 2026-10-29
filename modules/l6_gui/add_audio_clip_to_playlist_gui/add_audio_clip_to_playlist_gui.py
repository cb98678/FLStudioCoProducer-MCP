from __future__ import annotations

from coproducer import call
from coproducer.result import Result


def add_audio_clip_to_playlist_gui(track: int = 1) -> Result:
    """Place the selected Audio Clip channel on a playlist track at bar 1 with a paint click.

    The playlist must show the paint tool, and the channel to place must be the selected one (a fresh import is).
    Errors: E_GUI_MISMATCH, E_HALTED, E_UNSUPPORTED_API for a draft recipe.
    """
    return call("run_gui_recipe", name="place_audio_clip_gui", params={"track": track})
