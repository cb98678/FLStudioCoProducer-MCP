from __future__ import annotations

from coproducer import call
from coproducer.result import Result
from coproducer.services import get_service


def import_audio_clip_gui(path: str) -> Result:
    """Load a sandbox audio file into a new Audio Clip channel of the open FL project.

    Runs the recipe of the same name: channel rack add menu, Audio Clip, the file button, the path typed in the open dialog.
    The clip still has to be placed in the playlist. Errors: E_SANDBOX_VIOLATION, E_GUI_MISMATCH, E_BLOCKED_BY_DIALOG, E_HALTED.
    """
    chk = call("check_sandbox_path", path=path, sandbox_root=str(get_service("sandbox_root")))
    if not chk.ok:
        return chk
    return call("run_gui_recipe", name="import_audio_clip_gui", params={"path": chk.value["resolved"]})
