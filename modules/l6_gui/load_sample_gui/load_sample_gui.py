from __future__ import annotations

from coproducer import call
from coproducer.result import Result


def load_sample_gui(filename: str) -> Result:
    """Load a sample into the channel rack by searching the sample browser.

    Runs the recipe of the same name. Draft recipes need desktop.allow_unverified. Errors: E_GUI_MISMATCH, E_BLOCKED_BY_DIALOG, E_HALTED.
    """
    return call("run_gui_recipe", name="load_sample_gui", params={'filename': filename})
