from __future__ import annotations

import json
import shutil
from pathlib import Path

from coproducer import call, remixaudio, songplan
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def prepare_remix_audio(plan_file: str, vocals_path: str, out_dir: str, cuts_file: str = "", pitch_ratio: float = 0.0, other_path: str = "") -> Result:
    """Write the audio folder build_remix_project reads, for one song plan: the vocal stem stretched to the remix tempo (times the plan's vocal
    multiple, rubberband through ffmpeg with formants kept), each chop as a one-shot on its syllable onsets (cuts_file holds recogniser-checked cut
    points from tools/refine_cuts.py), the echo versions, the plan style's drum kit and bass sample (A1 on key 60), and the FX bed at the cues.
    pitch_ratio 0 takes the plan's correction; other_path is the original's instrumentation stem when the plan plays it. Errors: E_SANDBOX_VIOLATION,
    E_NOT_FOUND, E_ARG (bad plan), E_IO (ffmpeg, or a stem the plan plays is missing), E_NOT_VERIFIED.
    """
    chk = call("check_sandbox_path", path=out_dir, sandbox_root=str(get_service("sandbox_root")))
    if not chk.ok:
        return chk
    for p in (plan_file, vocals_path) + ((cuts_file,) if cuts_file else ()) + ((other_path,) if other_path else ()):
        if not Path(p).is_file():
            return fail("E_NOT_FOUND", "no file at %s" % Path(p).name)
    if not shutil.which("ffmpeg"):
        return fail("E_IO", "ffmpeg is not on PATH (the full build carries the rubberband filter)")
    try:
        songplan.apply(songplan.load(plan_file))
        info = remixaudio.prepare(chk.value["resolved"], vocals_path, cuts_file, pitch_ratio or None, log=lambda *a: None,
                                  stems={"other": other_path} if other_path else None)
    except songplan.PlanError as e:
        return fail("E_ARG", str(e))
    except (remixaudio.AudioError, OSError, ValueError) as e:
        return fail("E_IO", "%s: %s" % (type(e).__name__, e))
    meta = Path(chk.value["resolved"]) / "techhouse_audio.json"
    back = json.loads(meta.read_text(encoding="utf-8")) if meta.is_file() else {}
    missing = [c["file"] for c in back.get("chops", {}).values() if not (Path(chk.value["resolved"]) / c["file"]).is_file()]
    return ok({"out_dir": chk.value["resolved"], "style": info.get("style"), "stretch": info["stretch"], "chops": len(info["chops"]),
               "vocal_seconds": info["vocal_seconds"]}, verified=bool(back) and not missing)
