"""Song intake: the facts a remix plan needs, from the stems and the model outputs of one song, written as the files build_song_plan reads.

The module build_song_analysis runs the models (separation, beats, words, melody); this file turns their output into the bar grid, the drum
entrance, the bass key and roots per bar, a vote between three independent key estimates, and the song's own section map. Nothing here runs a
model, so each step is testable on stored outputs (tests/data). Key estimates disagree often (on the Friends chorus the sung melody alone reads
E major, the bass A major): the vote keeps all three and says how sure it is, and a split vote goes to the person.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np

from . import bassnotes, beatgrid, drumhits, dsp, songanalysis

NAMES = bassnotes.NAMES


def drum_hits(drums_path: str, grid: dict) -> dict:
    """drum_hits.json content: hits [t, kind, strength] from the drum stem, the grid tempo, the bar line the drums enter on (origin_s)."""
    x, rate = dsp.load_audio(drums_path)
    hits = drumhits.detect_hits(dsp.mono(x), rate)
    rows = [[round(h["t"], 4), drumhits.classify(h), round(float(h["strength"]), 3)] for h in hits]
    first = next((r[0] for r in rows if r[1] in ("kick", "snare")), rows[0][0] if rows else grid["origin_s"])
    bar = beatgrid.first_bar_after(grid, first)
    origin = grid["bars"][min(bar, len(grid["bars"]) - 1)]
    return {"file": Path(drums_path).name, "from_grid": True, "bpm": grid["bpm"], "offset_s": round(origin % (60.0 / grid["bpm"] / 4), 4), "origin_s": origin,
            "first_hit_s": first, "counts": dict(Counter(r[1] for r in rows)), "hits": rows}


def roots_on_bars(notes: list[dict], bars: list[float]) -> list[int | None]:
    """The pitch class holding the most note time in each bar between consecutive bar lines (a drifting song keeps its own bars)."""
    out: list[int | None] = []
    for t0, t1 in zip(bars, bars[1:]):
        w = np.zeros(12)
        for n in notes:
            ov = min(n["end"], t1) - max(n["start"], t0)
            if ov > 0:
                w[n["pitch"] % 12] += ov
        out.append(int(np.argmax(w)) if w.sum() > 0.2 * (t1 - t0) else None)
    return out


def bass_facts(bass_path: str, grid: dict, origin_s: float) -> dict:
    """stem_notes.json "bass" content: notes, key, and a root per bar counted from 12 bars before origin_s (the layout tools/stem_notes.py wrote)."""
    x, rate = dsp.load_audio(bass_path)
    t, m, lv = bassnotes.track_pitch(dsp.mono(x), rate)
    notes = bassnotes.notes_from_track(t, m, lv)
    if not notes:
        return {"notes": [], "key": None, "roots_per_bar": []}
    bar_s = 60.0 * grid["meter"] / grid["bpm"]
    first = int(np.searchsorted(np.asarray(grid["bars"]), origin_s - 12 * bar_s - 0.05))
    lines = grid["bars"][first:] + [grid["bars"][-1] + bar_s]
    roots = roots_on_bars(notes, lines)
    return {"key": bassnotes.estimate_key(notes), "roots_per_bar": [None if r is None else NAMES[r] for r in roots], "notes": len(notes),
            "bar0_s": lines[0]}


def key_vote(bass_key: dict | None, melody_key: dict | None, dsp_key: dict | None) -> dict:
    """Vote between the bass, the sung melody and the whole-mix DSP estimate. A key counts as the same when tonic and mode match, or when one is
    the other's dominant in major (a chorus that sits on V reads as V): the bass gets two votes, since harmony is anchored there. Returns the
    choice, how many agree and whether the person should be asked."""
    cands = []
    if bass_key:
        cands += [("bass", bass_key["tonic_pc"], bass_key["mode"])] * 2
    if melody_key:
        cands.append(("melody", melody_key["tonic"], melody_key["mode"]))
    if dsp_key and dsp_key.get("key"):  # estimate_key_dsp: {"key": "A major", ...}
        tonic, _, mode = dsp_key["key"].partition(" ")
        if tonic in NAMES:
            cands.append(("mix", NAMES.index(tonic), mode or "major"))
    if not cands:
        return {"tonic_pc": None, "ask": True, "why": "no key estimate"}
    score: Counter = Counter()
    for _who, pc, mode in cands:
        score[(pc, mode)] += 1.0
        if mode == "major":
            score[((pc - 7) % 12, "major")] += 0.5  # V of the true key
    (pc, mode), s = score.most_common(1)[0]
    agree = sorted({who for who, p, m in cands if (p, m) == (pc, mode) or (m == "major" and (p - 7) % 12 == pc)})
    return {"tonic_pc": pc, "mode": mode, "name": "%s %s" % (NAMES[pc], mode), "agree": agree, "votes": [list(c) for c in cands],
            "ask": len(agree) < 2, "why": "" if len(agree) >= 2 else "the estimates disagree; ask the person"}


def bar_levels(path: str, bars: list[float]) -> list[float]:
    x, rate = dsp.load_audio(path)
    m = dsp.mono(x)
    out = []
    for t0, t1 in zip(bars, bars[1:]):
        seg = m[int(t0 * rate) : int(t1 * rate)]
        out.append(round(float(20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9)), 2) if len(seg) else -120.0)
    return out


def source_sections(mix_path: str, grid: dict, words: list[dict], hook_words: str = "") -> list[dict]:
    """The song's own section map in its bars: level jumps of the mix, labelled chorus where the hook's words are sung, verse where other words are."""
    bars = grid["bars"]
    db = bar_levels(mix_path, bars)
    toks = songanalysis.tokens(words)
    sung = {int(beatgrid.time_to_bar(grid, t["t0"])) for t in toks}
    hook = set(hook_words.lower().split()) - songanalysis.STOP
    hook_bars = {int(beatgrid.time_to_bar(grid, t["t0"])) for t in toks if t["w"] in hook} if hook else set()
    return songanalysis.sections_from_bars(db, sung, hook_bars)


def write_files(folder: str | Path, words: dict, hits: dict, bass: dict, analysis: dict) -> dict:
    """vocal_words.json, drum_hits.json, stem_notes.json and song_analysis.json in folder; returns their paths."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    paths = {"words": folder / "vocal_words.json", "hits": folder / "drum_hits.json", "bass": folder / "stem_notes.json", "analysis": folder / "song_analysis.json"}
    paths["words"].write_text(json.dumps(words, indent=1), encoding="utf-8")
    paths["hits"].write_text(json.dumps(hits), encoding="utf-8")
    paths["bass"].write_text(json.dumps({"bpm": hits["bpm"], "origin_s": hits["origin_s"], "bass": bass}), encoding="utf-8")
    paths["analysis"].write_text(json.dumps(analysis, indent=1), encoding="utf-8")
    return {k: str(v) for k, v in paths.items()}


def loop_windows(words: list[dict], vocals: str) -> tuple[list, list]:
    """(loop spans, redo windows) for Whisper's repetition loops in words, the windows on the vocal stem's own phrases (asrclean)."""
    from . import asrclean, vocalchops
    spans = asrclean.loop_spans(words)
    if not spans:
        return [], []
    import soundfile as sf
    x, rate = sf.read(vocals, dtype="float32", always_2d=True)
    return spans, asrclean.windows(spans, vocalchops.phrases(x.mean(axis=1), rate))


def splice_words(value: dict, spans: list, redone: list[dict]) -> tuple[dict, dict]:
    """The transcript with the loop spans replaced by the redone words (asrclean.splice); (value, report)."""
    from . import asrclean
    new, rep = asrclean.splice(value["words"], spans, redone)
    return {**value, "words": new, "text": " ".join(w["word"] for w in new), "asr_cleanup": rep}, rep
