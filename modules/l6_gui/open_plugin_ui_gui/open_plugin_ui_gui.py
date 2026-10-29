from __future__ import annotations

from coproducer import call
from coproducer.result import Result


def open_plugin_ui_gui(target: str) -> Result:
    """Open the window of a plugin so its controls can be reached.

    Runs the recipe of the same name. Draft recipes need desktop.allow_unverified. Errors: E_GUI_MISMATCH, E_BLOCKED_BY_DIALOG, E_HALTED.
    """
    return call("run_gui_recipe", name="open_plugin_ui_gui", params={'target': target})
