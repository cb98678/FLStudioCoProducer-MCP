from __future__ import annotations

import json
from pathlib import Path

from coproducer import call, loopsets
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def extract_song_loops(song_dir: str, sections: str, out_dir: str = "", loop_bars: list | None = None, kit_from: str = "", hook: str = "") -> Result:
    """Cut a song's loops, drum kit and patterns from its stems (a build_song_analysis folder): per section ("name:first-last" bars, comma
    separated) the drum, bass, music and full loops with every repetition aligned and averaged so the bleed cancels, the three-band drum
    pattern and the bass notes (MIDI files too); a kick, clap or snare and hat averaged from many hits (a clap on the kick comes back
    without it); hook: vocal bars to cut. Writes under the sandbox (default sandbox/loops/SONG); verified when patterns.json reads back.
    Errors: E_NOT_FOUND (no analysis or drum stem), E_ARG (bad sections), E_SANDBOX_VIOLATION."""
    folder = Path(song_dir)
    root = str(get_service("sandbox_root"))
    out = Path(out_dir) if out_dir else Path(root) / "loops" / folder.name
    chk = call("check_sandbox_path", path=str(out), sandbox_root=root)
    if not chk.ok:
        return chk
    if not (folder / "song_analysis.json").is_file():
        return fail("E_NOT_FOUND", "no song_analysis.json in %s: run build_song_analysis first" % folder.name)
    try:
        rep = loopsets.extract(folder, sections, out, loop_bars=loop_bars or [1, 2, 4], kit_from=kit_from, hook=hook)
    except loopsets.LoopError as e:
        return fail("E_NOT_FOUND" if "drum stem" in str(e) else "E_ARG", str(e))
    secs = {k: {"bars": v["bars"], "drums": v["drums"], "bass_notes": v.get("bass_notes", []),
                "loops": {n: lp.get("file") or ("silent" if lp.get("silent") else lp.get("skipped", "")) for n, lp in v["loops"].items()}}
            for k, v in rep["sections"].items()}
    kit = {k: {"file": v["file"], "hits": v["n"], "pitch_hz": v.get("pitch_hz"), "decay_ms": v["decay_ms"]} for k, v in rep["kit"].items()}
    back = json.loads((out / "patterns.json").read_text(encoding="utf-8"))
    good = back.get("sections", {}).keys() == rep["sections"].keys() and all(Path(f).is_file() for f in rep["files"])
    return ok({"out_dir": str(out), "bpm": rep["bpm"], "files": len(rep["files"]), "sections": secs, "kit": kit, "readme": str(out / "README.md")},
              verified=bool(good))
