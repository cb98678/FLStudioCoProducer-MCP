from __future__ import annotations

import shutil
from pathlib import Path

from coproducer import automation as A
from coproducer import call
from coproducer.flpfile import Flp, FlpError
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def add_automation_clip(project: str, name: str, target: dict, curve: dict, unit: str = "knob", start_beat: float = 0.0,
                        playlist_track: int | None = None) -> Result:
    """Add one automation clip to a project inside the sandbox. Value units: knob 0..1 (volume 0.8 is 0 dB) or db for track_volume.

    The project must have been saved by FL itself. A copy of the file is kept once as <name>.pre_automation.flp.
    Errors: E_NOT_FOUND, E_SANDBOX_VIOLATION, E_ARG for a bad target or curve, E_NOT_VERIFIED if the clip does not read back.
    """
    root, path = get_service("sandbox_root"), Path(project)
    if root is None or not call("check_sandbox_path", path=str(path), sandbox_root=str(root)).ok:
        return fail("E_SANDBOX_VIOLATION", "the project must be inside the sandbox folder")
    if not path.is_file():
        return fail("E_NOT_FOUND", "no project file at that path")
    try:
        flp, (link, bipolar), pts = Flp.load(path), A.resolve_target(target), A.curve_points(curve, unit)
        cid, trk = A.next_channel_id(flp), playlist_track or A.first_free_track(flp)
        backup = path.with_name(path.stem + ".pre_automation.flp")
        if not backup.exists():
            shutil.copy2(path, backup)
        A.add_automation_clip(flp, cid, name, link, pts, start_beat=start_beat, track=trk, bipolar=bipolar)
        flp.save(path)
        back = next((c for c in A.list_automation(Flp.load(path)) if c["channel"] == cid), None)
    except (FlpError, KeyError, ValueError, TypeError) as e:
        return fail("E_ARG", str(e))
    if back is None or back["link"] != link or len(back["points"]) != len(pts):
        return fail("E_NOT_VERIFIED", "the clip did not read back from the saved file")
    return ok({"channel": cid, "playlist_track": trk, "link": hex(link), "points": len(pts), "length_beats": pts[-1][0], "backup": str(backup)}, verified=True)
