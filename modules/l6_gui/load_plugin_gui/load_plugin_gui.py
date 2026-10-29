from __future__ import annotations

from coproducer import call
from coproducer.result import Result


def load_plugin_gui(name: str) -> Result:
    """Add a plugin to the channel rack by name through the plugin picker.

    Runs the recipe of the same name. Draft recipes need desktop.allow_unverified. Errors: E_GUI_MISMATCH, E_BLOCKED_BY_DIALOG, E_HALTED.
    """
    return call("run_gui_recipe", name="load_plugin_gui", params={'name': name})
