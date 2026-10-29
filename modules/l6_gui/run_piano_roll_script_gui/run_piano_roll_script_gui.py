from __future__ import annotations

from coproducer import call
from coproducer.result import Result


def run_piano_roll_script_gui() -> Result:
    """Run the armed piano roll script again and confirm it closed cleanly.

    Runs the recipe of the same name. Draft recipes need desktop.allow_unverified. Errors: E_GUI_MISMATCH, E_BLOCKED_BY_DIALOG, E_HALTED.
    """
    return call("run_gui_recipe", name="run_piano_roll_script_gui", params={})
