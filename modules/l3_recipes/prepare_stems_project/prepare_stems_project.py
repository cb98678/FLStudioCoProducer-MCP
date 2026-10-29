from __future__ import annotations

from pathlib import Path

import soundfile as sf

from coproducer import call
from coproducer.flpfile import Flp, FlpError
from coproducer.result import Result, fail, ok
from coproducer.services import get_service

PARTS = ("drums", "bass", "instruments", "vocals")   # FL's four stems, named <sample>_<part>.wav in the data folder's Audio folder


def _template(given: str, root: Path) -> Path | None:
    for p in ([Path(given)] if given else [root / "stemstest" / "stemstest.flp", root / "templates" / "base_project.flp"]):
        if p.is_file():
            return p
    return None


def prepare_stems_project(song: str, out_project: str, template: str = "") -> Result:
    """Write a small sandbox project for FL's "Extract stems from sample": the song as one audio clip at the start of playlist track 1, every
    playlist row plain (enabled, ungrouped, unnamed), the data folder set to out_project's folder (FL writes the stems to its Audio subfolder).
    Made from an FL-saved project with an audio clip (default sandbox\\stemstest\\stemstest.flp, else sandbox\\templates\\base_project.flp).
    Returns project, data_folder, expected (part: path of each stem FL will write) and ready (every stem there and newer than the song).
    Errors: E_SANDBOX_VIOLATION, E_NOT_FOUND, E_ARG (a template without an audio clip).
    """
    root = Path(str(get_service("sandbox_root")))
    checks = [call("check_sandbox_path", path=p, sandbox_root=str(root)) for p in (song, out_project)]
    bad = next((c for c in checks if not c.ok), None)
    if bad is not None:
        return bad
    src, out = Path(checks[0].value["resolved"]), Path(checks[1].value["resolved"])
    tmpl = _template(template, root)
    if not src.is_file() or tmpl is None:
        return fail("E_NOT_FOUND", "no song at %s or no template project" % src.name)
    try:
        f = Flp.load(tmpl)
        ch = next(c for c in f.channel_ids() if f.channel_info(c)["sample"] and any(int.from_bytes(it[6:8], "little") == c for it in f.playlist_items()))
        layout = f.audio_item(ch)
        f.clear_playlist()
        f.reset_playlist_tracks()
        f.set_sample(ch, str(src), name="Song")
        f.set_data_folder(str(out.parent))
        ticks = int(round(sf.info(str(src)).duration / (60.0 / f.tempo() / f.ppq)))
        f.add_audio_clips(ch, 0, [(0, ticks, -1.0, -1.0)], layout)
        out.parent.mkdir(parents=True, exist_ok=True)
        f.save(out)
    except (FlpError, StopIteration, RuntimeError) as e:
        return fail("E_ARG", "cannot make a stems project from %s: %s" % (tmpl.name, e))
    expected = {p: str(out.parent / "Audio" / ("%s_%s.wav" % (src.stem, p))) for p in PARTS}
    ready = all(Path(v).is_file() and Path(v).stat().st_mtime >= src.stat().st_mtime for v in expected.values())
    return ok({"project": str(out), "data_folder": str(out.parent), "expected": expected, "ready": ready, "template": str(tmpl), "channel": ch})
