from __future__ import annotations

from coproducer import call
from coproducer.result import Result
from coproducer.services import get_service


def open_project_copy(path: str) -> Result:
    """Open a project file that lives inside the sandbox.

    Runs the recipe of the same name. Draft recipes need desktop.allow_unverified. Errors: E_GUI_MISMATCH, E_BLOCKED_BY_DIALOG, E_HALTED.
    """
    root = get_service("sandbox_root")
    chk = call("check_sandbox_path", path=path, sandbox_root=str(root))
    if not chk.ok:
        return chk
    return call("run_gui_recipe", name="open_project_copy", params={'path': path})
