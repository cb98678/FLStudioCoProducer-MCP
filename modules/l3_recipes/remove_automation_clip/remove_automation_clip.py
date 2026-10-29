from __future__ import annotations

import shutil
from pathlib import Path

from coproducer import automation as A
from coproducer import call
from coproducer.flpfile import Flp, FlpError
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def remove_automation_clip(project: str, channel: int) -> Result:
    """Remove the automation clip with this channel id (see list_automation_clips). Other channels are never touched.

    Errors: E_NOT_FOUND, E_SANDBOX_VIOLATION, E_ARG when the channel is not an automation clip, E_NOT_VERIFIED if it is still listed.
    """
    root, path = get_service("sandbox_root"), Path(project)
    if root is None or not call("check_sandbox_path", path=str(path), sandbox_root=str(root)).ok:
        return fail("E_SANDBOX_VIOLATION", "the project must be inside the sandbox folder")
    if not path.is_file():
        return fail("E_NOT_FOUND", "no project file at that path")
    try:
        flp = Flp.load(path)
        if channel not in [c["channel"] for c in A.list_automation(flp)]:
            return fail("E_ARG", "channel %d is not an automation clip in this project" % channel)
        backup = path.with_name(path.stem + ".pre_automation.flp")
        if not backup.exists():
            shutil.copy2(path, backup)
        A.remove_automation_clip(flp, channel)
        flp.save(path)
        left = [c["channel"] for c in A.list_automation(Flp.load(path))]
    except (FlpError, ValueError) as e:
        return fail("E_ARG", str(e))
    if channel in left:
        return fail("E_NOT_VERIFIED", "the clip is still in the saved file")
    return ok({"removed": channel, "remaining": left, "backup": str(backup)}, verified=True)
