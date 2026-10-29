from __future__ import annotations

from coproducer import call
from coproducer.result import Result


def add_mixer_insert_gui(track_label: str, plugin: str) -> Result:
    """Add a plugin to an effect slot of a mixer track.

    Runs the recipe of the same name. Draft recipes need desktop.allow_unverified. Errors: E_GUI_MISMATCH, E_BLOCKED_BY_DIALOG, E_HALTED.
    """
    return call("run_gui_recipe", name="add_mixer_insert_gui", params={'track_label': track_label, 'plugin': plugin})
