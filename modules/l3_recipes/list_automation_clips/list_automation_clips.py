from __future__ import annotations

from pathlib import Path

from coproducer.automation import decode_link, list_automation
from coproducer.flpfile import Flp, FlpError
from coproducer.result import Result, fail, ok


def list_automation_clips(project: str) -> Result:
    """List automation clips in an .flp file. Points are (beat, value) with value the knob position 0..1 (0.8 is 0 dB on a volume).

    Errors: E_NOT_FOUND no file, E_ARG when the file is not a readable FL project.
    """
    path = Path(project)
    if not path.is_file():
        return fail("E_NOT_FOUND", "no project file at that path")
    try:
        clips = list_automation(Flp.load(path))
    except (FlpError, ValueError, OSError) as e:
        return fail("E_ARG", "not a readable FL project: %s" % e)
    for c in clips:
        c["target"] = decode_link(c["link"]) if c["link"] else None
        c["points"] = [{"beat": round(b, 4), "value": round(v, 4)} for b, v, _ in c["points"]]
    return ok({"clips": clips, "count": len(clips)})
