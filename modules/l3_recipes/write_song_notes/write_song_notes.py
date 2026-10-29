from __future__ import annotations

import json
import re
from pathlib import Path

from coproducer import call
from coproducer.result import Result, fail, ok
from coproducer.services import get_service

REQUIRED = ("title", "artist", "form", "mood", "favorites", "sources")
RUN = 6  # this many words in a row shared with the song's own transcript is lyrics


def _strings(x) -> list[str]:
    if isinstance(x, str):
        return [x]
    if isinstance(x, dict):
        return [s for v in x.values() for s in _strings(v)]
    if isinstance(x, list):
        return [s for v in x for s in _strings(v)]
    return []


def write_song_notes(out_file: str, notes: dict, words_file: str = "") -> Result:
    """Write song_notes.json: title, artist, form (the parts in order, in words), mood ({feel: one or two words such as happy, sad, romantic,
    angry, playful; evidence: what says so}: the remix matches the song's tone, 2026-10-26), favorites ([{what, use, source}]: what fans love and what the
    remix does with it), sources (links). With words_file (the song's own transcript) a note sharing six or more words in a row with it is
    refused: lyrics are never copied from the web into the project; the words come from the person's file. Errors: E_SANDBOX_VIOLATION, E_ARG.
    """
    chk = call("check_sandbox_path", path=out_file, sandbox_root=str(get_service("sandbox_root")))
    if not chk.ok:
        return chk
    missing = [k for k in REQUIRED if not notes.get(k)]
    if missing:
        return fail("E_ARG", "song notes need %s" % ", ".join(missing))
    if not all(isinstance(f, dict) and f.get("what") and f.get("source") for f in notes["favorites"]):
        return fail("E_ARG", "each favorite needs what and source")
    mood = notes["mood"]
    if not (isinstance(mood, dict) and mood.get("feel") and mood.get("evidence")):
        return fail("E_ARG", "mood needs feel (happy, sad, romantic, angry, playful...) and evidence (the lyrics' themes, key and mode, delivery, sources)")
    if words_file and Path(words_file).is_file():
        sung = [re.sub(r"[^a-z']", "", str(w["word"]).lower()) for w in json.loads(Path(words_file).read_text(encoding="utf-8"))["words"]]
        runs = {" ".join(sung[i : i + RUN]) for i in range(len(sung) - RUN + 1)}
        for text in _strings(notes):
            ws = [w for w in (re.sub(r"[^a-z']", "", t) for t in text.lower().split()) if w]
            if any(" ".join(ws[i : i + RUN]) in runs for i in range(len(ws) - RUN + 1)):
                return fail("E_ARG", "a note repeats %d or more words of the lyrics in a row; describe the part instead of quoting it" % RUN)
    out = Path(chk.value["resolved"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(notes, indent=1, ensure_ascii=False), encoding="utf-8")
    return ok({"out_file": str(out), "favorites": len(notes["favorites"]), "form": notes["form"]}, verified=out.is_file())
