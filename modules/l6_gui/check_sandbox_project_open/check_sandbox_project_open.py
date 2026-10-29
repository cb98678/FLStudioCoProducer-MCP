from __future__ import annotations

from pathlib import Path

from coproducer import call
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def check_sandbox_project_open() -> Result:
    """Check that the project open in FL is a saved .flp file that lives inside the sandbox, judged by the window title.

    Errors: E_SANDBOX_VIOLATION when the title has no .flp name or no sandbox file has that name; desktop errors pass through.
    """
    ready = call("check_desktop_ready")
    if not ready.ok:
        return ready
    shown = ready.value["title"].split(" - ")[0].strip().rstrip("*").strip()
    if not shown.lower().endswith(".flp"):
        return fail("E_SANDBOX_VIOLATION", "the open FL project has no file name (%r); open a sandbox copy first" % shown)
    root = Path(str(get_service("sandbox_root")))
    hit = next((p for p in root.rglob(shown) if p.is_file() and "Backup" not in p.parts), None)
    if hit is None:
        return fail("E_SANDBOX_VIOLATION", "the open project %r is not a file in the sandbox; nothing was clicked" % shown)
    return ok({"project": shown, "path": str(hit)})
