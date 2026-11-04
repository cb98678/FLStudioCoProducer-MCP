from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from coproducer import call, dsp, newtimeview, vocalchunk
from coproducer.result import Result, fail, ok
from coproducer.services import get_service

DEFAULTS = {"floor_under_db": vocalchunk.FLOOR_UNDER_DB, "phrase_gap_s": vocalchunk.PHRASE_GAP_S, "min_gap_s": vocalchunk.MIN_GAP_S,
            "max_beats": vocalchunk.MAX_BEATS, "max_move_s": 0.045, "stem": "chunk"}


def _words(words_path: str, root: str):
    if not words_path:
        return ok([])
    wp = call("check_sandbox_path", path=words_path, sandbox_root=root)
    if not wp.ok:
        return wp
    try:
        d = json.loads(Path(wp.value["resolved"]).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return fail("E_IO", "cannot read the words file: %s" % e)
    return ok(d["words"] if isinstance(d, dict) else d)


def split_vocal_phrases(path: str, out_dir: str, bpm: float, origin_s: float = 0.0, words_path: str = "", lead_s: float = -1.0, options: dict | None = None) -> Result:
    """Cut a long vocal into phrase chunks for Newtime and Newtone (skill vocal-chunking): one file per phrase, cut only in the silences
    between phrases (never inside a word or a syllable: the words file keeps a stop consonant's closure whole), through each last word's
    release, every file starting on a grid line of the song (bpm, origin_s = beat 0 in the file) so Newtime's grid is the project's and the
    manifest's `beat` is the chunk's playlist position. words_path: the transcript on the file's clock; lead_s negative measures the lead.
    options: floor_under_db (30, the silence floor under the loud level), phrase_gap_s (0.25), min_gap_s (0.15), max_beats (16), max_move_s (0.045, flags a chunk off the grid as a
    whole), stem. Writes STEM_NN.wav and chunks.json into out_dir. Errors: E_SANDBOX_VIOLATION, E_IO, E_ARG, E_NOT_FOUND (no voice).
    """
    root = str(get_service("sandbox_root"))
    src, dst = call("check_sandbox_path", path=path, sandbox_root=root), call("check_sandbox_path", path=out_dir, sandbox_root=root)
    if not src.ok or not dst.ok:
        return src if not src.ok else dst
    if not (40.0 <= bpm <= 250.0):
        return fail("E_ARG", "bpm must be 40..250")
    o = {**DEFAULTS, **(options or {})}
    try:
        x, rate = dsp.load_audio(src.value["resolved"])
    except ValueError as e:
        return fail("E_IO", str(e))
    got = _words(words_path, root)
    if not got.ok:
        return got
    words = got.value
    mono = x.mean(axis=1) if x.ndim == 2 else x
    onsets = newtimeview.onset_times(mono, rate)
    lead = newtimeview.best_lead(onsets, bpm, 4) if lead_s < 0 else float(lead_s)
    chunks = vocalchunk.plan(mono, rate, bpm, origin_s, words, onsets, float(o["floor_under_db"]), float(o["phrase_gap_s"]), float(o["min_gap_s"]),
                             float(o["max_beats"]), max_move_s=float(o["max_move_s"]))
    if not chunks:
        return fail("E_NOT_FOUND", "no voice in the file")
    folder = Path(dst.value["resolved"])
    vocalchunk.write_chunks(x, rate, chunks, folder, str(o["stem"]), tail_s=2 * 4 * 60.0 / bpm)
    man = vocalchunk.manifest(chunks, bpm, origin_s, src.value["resolved"], lead, rate, len(mono) / rate, {"words_path": words_path, "options": o})
    mp = folder / "chunks.json"
    mp.write_text(json.dumps(man, indent=1), encoding="utf-8")
    flat = [v for c in chunks for v in c.offsets_ms]
    return ok({"manifest": str(mp), "chunks": len(chunks), "files": [c.file for c in chunks], "lead_s": lead, "onsets": int(len(onsets)),
               "median_offset_ms": (round(float(np.median(np.abs(flat))), 1) if flat else None),
               "flagged": [{"index": c.index, "flags": c.flags, "text": " ".join(c.words)} for c in chunks if c.flags],
               "words_placed": sum(len(c.words) for c in chunks), "words_total": len(words)})
