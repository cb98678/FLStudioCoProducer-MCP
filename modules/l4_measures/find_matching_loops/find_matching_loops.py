from __future__ import annotations

import json
from pathlib import Path

from coproducer import loopsets
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def find_matching_loops(patterns_path: str, section: str, folders: list | None = None, kick_path: str = "", kick_folders: list | None = None,
                        top: int = 10) -> Result:
    """Rank drum loops on this computer by how closely their kick, snare or clap and hat step patterns match one section of a song's
    extract_song_loops patterns.json (tempo is not compared: FL stretches a loop to the project), and with kick_path rank kick samples by
    pitch, decay and click. Without folders it searches FL Studio's factory Packs (Loops, Legacy Loops; kicks in Drums Kicks and the legacy
    dance and FPC kicks). Reads only; nothing is downloaded or copied.
    Errors: E_NOT_FOUND (no patterns file, no folder to search), E_ARG (no such section)."""
    p = Path(patterns_path)
    if not p.is_file():
        return fail("E_NOT_FOUND", "no patterns file at %s: run extract_song_loops first" % p.name)
    packs = loopsets.fl_packs(get_service("fl_exe", None))
    look = [Path(f) for f in folders or []] or ([packs / s for s in loopsets.PACK_LOOPS] if packs else [])
    kfold = [Path(f) for f in kick_folders or []] or ([packs / s for s in loopsets.PACK_KICKS] if packs else [])
    if not any(f.is_dir() for f in look):
        return fail("E_NOT_FOUND", "no folder to search (FL Studio's Packs were not found; pass folders)")
    if kick_path and not Path(kick_path).is_file():
        return fail("E_NOT_FOUND", "no kick sample at %s" % Path(kick_path).name)
    rep = json.loads(p.read_text(encoding="utf-8"))
    try:
        res = loopsets.find(rep, section, look, kick_path or None, kfold, top)
    except loopsets.LoopError as e:
        return fail("E_ARG", str(e))
    return ok({**res, "folders": [str(f) for f in look], "summary": loopsets.found_markdown(res, rep.get("name", p.parent.name), look)})
