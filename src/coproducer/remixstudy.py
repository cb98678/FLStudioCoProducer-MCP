"""Study a professional remix against its original (skill remix-craft, references/study-protocol.md): where each sung line of the original
went in the remix (whole, cut down, or chopped and repeated), the tempo and key change, and the remix's energy in 8-bar blocks with the vocal
lines that play in each. Inputs are two build_song_analysis folders (vocal_words.json and song_analysis.json); the energy curve reads the
mix itself. It reads; it never writes the person's files. What only ears can judge (the new chords, the sounds, why a move works) is left
to the reading the skill asks for.
"""
from __future__ import annotations

import difflib
import json
import math
from pathlib import Path

from . import songanalysis, songform

MATCH = 0.6      # the share of an original line's words a remix line must reproduce in order to count as that line
WHOLE = 0.8      # a remix line holding this share of the original line's words is the line sung whole
CHOP_WORDS = 3   # a matched remix line of this many words or fewer is a chop


def load(folder: Path | str) -> dict:
    """{"words": tokens, "lines": sung lines, "bpm", "key", "title", "song"} of one analysis folder."""
    f = Path(folder)
    info = json.loads((f / "song_analysis.json").read_text(encoding="utf-8"))
    toks = songform.good(songanalysis.tokens(json.loads((f / "vocal_words.json").read_text(encoding="utf-8"))["words"]))
    key = info.get("key") or {}
    return {"words": toks, "lines": songform.lines(toks), "bpm": float((info.get("grid") or {}).get("bpm") or 0.0),
            "bars": (info.get("grid") or {}).get("bars") or [], "key": key.get("name"), "mix_key": (info.get("mix_key") or {}).get("key"),
            "title": info.get("title") or info.get("name") or f.name, "song": info.get("song")}


def _norm(w: str) -> str:
    return w.replace("'", "").rstrip("s")


def best_line(words: list[str], lines: list[dict]) -> tuple[int | None, float]:
    """The original line a remix line reproduces, and the share of that line's words it holds in order. A long remix line counts when it
    holds MATCH of the original line; a short one (a chop) when nearly all its own words come from one line. (None, 0) otherwise."""
    if len(words) < 2:
        return None, 0.0
    a = [_norm(w) for w in words]
    best, best_score, best_share = None, 0.0, 0.0
    for i, ln in enumerate(lines):
        b = [_norm(w) for w in ln["words"]]
        if len(b) < 2:
            continue
        hit = sum(m.size for m in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks())
        if hit < 2:
            continue
        of_orig, of_remix = hit / len(b), hit / len(a)
        score = of_orig if of_orig >= MATCH else (of_remix if len(a) <= CHOP_WORDS + 1 and of_remix >= 0.8 else 0.0)
        if score > best_score:
            best, best_score, best_share = i, score, of_orig
    return (best, round(best_share, 2)) if best is not None else (None, 0.0)


def treatment(share: float, n_words: int, repeats: int) -> str:
    if n_words <= CHOP_WORDS or repeats >= 3:
        return "chopped"
    return "whole" if share >= WHOLE else "cut down"


def map_lines(orig: dict, remix: dict) -> dict:
    """{"timeline": [{t0, t1, words, line, share, treatment}], "lines": [{line, words, t0, uses, first_s, treatments}]} for the remix's sung
    lines matched to the original's."""
    rows = []
    for ln in remix["lines"]:
        i, s = best_line(ln["words"], orig["lines"])
        rows.append({"t0": round(ln["t0"], 2), "t1": round(ln["t1"], 2), "words": " ".join(ln["words"]), "line": i, "share": s, "n": len(ln["words"])})
    counts: dict = {}
    for r in rows:
        if r["line"] is not None:
            counts[r["line"]] = counts.get(r["line"], 0) + 1
    for r in rows:
        r["treatment"] = treatment(r["share"], r["n"], counts.get(r["line"], 0)) if r["line"] is not None else "new or unmatched"
    per = []
    for i, ln in enumerate(orig["lines"]):
        used = [r for r in rows if r["line"] == i]
        per.append({"line": i, "words": " ".join(ln["words"]), "t0": round(ln["t0"], 2), "uses": len(used),
                    "first_s": used[0]["t0"] if used else None, "treatments": sorted({r["treatment"] for r in used})})
    return {"timeline": rows, "lines": per}


def tempo_change(orig_bpm: float, remix_bpm: float) -> dict:
    """The remix tempo as a stretch of the original: same, double, half or a percent change of the vocal's own tempo."""
    if not orig_bpm or not remix_bpm:
        return {"kind": "unknown"}
    best = min((("same", 1.0), ("double", 2.0), ("half", 0.5)), key=lambda kv: abs(math.log(remix_bpm / (orig_bpm * kv[1]))))
    stretch = remix_bpm / (orig_bpm * best[1]) - 1.0
    return {"kind": best[0] if abs(stretch) < 0.015 else "%s, vocal %+.1f%%" % (best[0], 100 * stretch), "ratio": round(remix_bpm / orig_bpm, 3),
            "vocal_stretch_pct": round(100 * stretch, 1)}


def blocks(x, rate: int, bars: list[float], bpm: float, size: int = 8) -> list[dict]:
    """Loudness of every `size`-bar block of a mix (bar times from the analysis grid, else the tempo from 0 s)."""
    from . import dsp
    bar_s = 240.0 / bpm if bpm else 2.0
    starts = list(bars) if bars else []
    end = len(x) / rate
    if not starts:
        starts = [k * bar_s for k in range(int(end / bar_s) + 1)]
    out = []
    for k in range(0, len(starts), size):
        a = starts[k]
        b = starts[k + size] if k + size < len(starts) else min(end, a + size * bar_s)
        seg = x[int(a * rate):int(b * rate)]
        if len(seg) < rate:
            continue
        out.append({"bar": k + 1, "t0": round(a, 2), "t1": round(b, 2), "lufs": round(dsp.integrated_loudness(seg, rate), 1)})
    return out


def with_vocals(blks: list[dict], timeline: list[dict]) -> list[dict]:
    """Each block with the original lines (by number) and the share of unmatched singing that fall in it."""
    for b in blks:
        inside = [r for r in timeline if b["t0"] <= r["t0"] < b["t1"]]
        b["lines"] = sorted({r["line"] for r in inside if r["line"] is not None})
        b["chops"] = sum(1 for r in inside if r["treatment"] == "chopped")
        b["new_singing"] = sum(1 for r in inside if r["line"] is None)
    return blks


def cue(words: str, n: int = 3) -> str:
    """The first few words of a line, to find it by: the page names lines, it does not reprint the lyrics."""
    w = words.split()
    return " ".join(w[:n]) + (" ..." if len(w) > n else "")


def report(orig: dict, remix: dict, mapping: dict, blks: list[dict], name: str = "") -> str:
    """The study page in Markdown: the numbers and the line map, with the questions left for the reading."""
    tc = tempo_change(orig["bpm"], remix["bpm"])
    used = [l for l in mapping["lines"] if l["uses"]]
    top = max((b["lufs"] for b in blks), default=0.0)
    L = ["# %s" % (name or "%s: remix study" % orig["title"]), "",
         "| | Original | Remix |", "| --- | --- | --- |",
         "| Tempo | %.2f | %.2f (%s) |" % (orig["bpm"], remix["bpm"], tc["kind"]),
         "| Key (votes) | %s | %s |" % (orig["key"], remix["key"]),
         "| Key (mix) | %s | %s |" % (orig["mix_key"], remix["mix_key"]),
         "| Sung lines | %d | %d |" % (len(orig["lines"]), len(remix["lines"])), "",
         "%d of the original's %d lines are heard in the remix; %d remix lines are chops (three words or fewer, or a line repeated three times or"
         " more) and %d match no original line (new singing, ad-libs or transcription errors)." % (
             len(used), len(orig["lines"]), sum(1 for r in mapping["timeline"] if r["treatment"] == "chopped"),
             sum(1 for r in mapping["timeline"] if r["line"] is None)), "",
         "## The original's lines in the remix", "", "| # | Line (its first words) | Sung at (original) | Uses | First at (remix) | How |", "| --- | --- | --- | --- | --- | --- |"]
    L += ["| %d | %s | %.1f s | %d | %s | %s |" % (l["line"] + 1, cue(l["words"]), l["t0"], l["uses"], "%.1f s" % l["first_s"] if l["first_s"] is not None else "-",
                                                ", ".join(l["treatments"]) or "absent") for l in mapping["lines"]]
    L += ["", "## The remix in 8-bar blocks", "", "| Bar | Time | LUFS | Under the peak | Original lines | Chops | Unmatched |", "| --- | --- | --- | --- | --- | --- | --- |"]
    L += ["| %d | %d:%02d | %.1f | %.1f | %s | %d | %d |" % (b["bar"], int(b["t0"]) // 60, int(b["t0"]) % 60, b["lufs"], top - b["lufs"],
                                                          " ".join(str(i + 1) for i in b["lines"]) or "-", b["chops"], b["new_singing"]) for b in blks]
    L += ["", "## For the reading (by ear)", "",
          "- The anchor: which line or part carries the remix, and was it the original's hook or something overlooked?",
          "- The harmony under the vocal: the same chords, the relative key, or a new progression?",
          "- The form in functions (mix in, verse, riserchorus, drop, breakdown, climax, mix out), and how drop two differs from drop one.",
          "- The sounds and the groove that make it a new record, and the one move that makes it work.", ""]
    return "\n".join(L)
