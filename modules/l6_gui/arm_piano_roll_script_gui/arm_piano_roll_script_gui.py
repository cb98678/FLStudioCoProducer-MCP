from __future__ import annotations

from coproducer import call
from coproducer.result import Result


def arm_piano_roll_script_gui(script: str) -> Result:
    """Open the piano roll and pick a script from its Tools menu.

    Runs the recipe of the same name. Draft recipes need desktop.allow_unverified. Errors: E_GUI_MISMATCH, E_BLOCKED_BY_DIALOG, E_HALTED.
    """
    return call("run_gui_recipe", name="arm_piano_roll_script_gui", params={'script': script})
