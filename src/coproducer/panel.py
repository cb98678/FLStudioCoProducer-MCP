"""The evaluation panel: independent judges of a remix, each kept to what it can actually know, and rules for when they must agree.

Judges, from most to least trusted:
  1. dsp: numbers measured on the render against the targets file (loudness, true peak, crest, section contrast, length against the plan).
  2. plan: facts that follow from the project itself (the style's drum grammar puts the snare on 3 in a dubstep drop); they answer the
     critic's questions before the critic does, so its answers can be graded.
  3. separation and similarity: how loud the voice is in the first drop by the vocal separation model (Mel-Band RoFormer), and how close
     the remix sounds to the person's reference tracks (MuQ-MuLan embeddings).
  4. critic: the audio-language model (Music Flamingo), asked narrow yes-or-no questions about short excerpts, never for a number.
A finding stands when a trusted judge reports it, or when two weaker judges agree. The critic is graded first on questions whose answers are
known (the rhythm from the plan; the voice from the separation model when it ran, since a vocal buried in the mix is not heard even where the plan
put it); below 0.75 its answers are listed and never counted (on the host it once described a drop in a 10 s clip that had none). Anything the
counted judges split on goes to the person.
"""
from __future__ import annotations

import re

YES = re.compile(r"^\W*(yes|yeah|correct|true)\b", re.I)
NO = re.compile(r"^\W*(no|not|false|incorrect)\b", re.I)


def yes_no(text: str) -> bool | None:
    """The critic's answer as True, False or None when it hedges."""
    t = (text or "").strip()
    if YES.match(t):
        return True
    if NO.match(t):
        return False
    return None


def plan_questions(style: dict) -> list[dict]:
    """Questions whose answers follow from the style pack, for grading the critic: [{"q", "expect"}]."""
    drop = style.get("drums", {}).get("drop", {}).get("bars", {})
    out = []

    def first(p):
        return p[0] if isinstance(p, list) else p
    k, sn = first(drop.get("kick", "")), first(drop.get("snare", "") or drop.get("clap", ""))
    if k:
        four = len(k) == 16 and all(k[i] in "Xxo" for i in (0, 4, 8, 12))
        out.append({"q": "In this excerpt, does the kick drum hit on every beat (four on the floor)? Answer yes or no first.", "expect": four,
                    "item": "four on the floor as planned"})
    if sn and len(sn) == 16:
        out.append({"q": "Does the snare or clap land only once per bar, on beat 3 (a half-time feel)? Answer yes or no first.",
                    "expect": [i for i, c in enumerate(sn) if c in "Xxo"] == [8], "item": "snare placement as planned"})
    # asked the inverse on purpose: Music Flamingo answered "no" to "is there a sung voice" on every clip, the isolated vocal stem included
    # (2 of 5 right), and "is this purely instrumental" right on all 5 (tools/critic_probe.py, 2026-10-25). yes here means no voice.
    out.append({"q": "Is this clip purely instrumental, with no human voice at all? Answer yes or no first.", "expect": None,  # filled by the caller
                "item": "voice audible in the first drop", "yes_means_voice": False})
    return out


def grade_critic(answers: list[dict]) -> dict:
    """answers: [{"q", "expect", "answer"}]. Share of plan questions the critic got right (hedges count as wrong), and the rows."""
    graded = [a for a in answers if a.get("expect") is not None]
    right = [a for a in graded if yes_no(a.get("answer", "")) == a["expect"]]
    return {"asked": len(graded), "right": len(right), "grade": round(len(right) / len(graded), 2) if graded else None,
            "trusted": bool(graded) and len(right) / len(graded) >= 0.75, "rows": answers}


def verdict(findings: list[dict], critic: dict | None = None) -> dict:
    """findings: [{"judge": dsp|plan|similarity|critic, "item", "ok": bool, "detail"}]. Returns problems that stand, items to ask the person,
    and the notes the panel does not act on."""
    trusted = {"dsp", "plan"}
    critic_ok = bool(critic and critic.get("trusted"))
    by_item: dict[str, list[dict]] = {}
    for f in findings:
        by_item.setdefault(f["item"], []).append(f)
    stand, ask, notes = [], [], []
    for item, rows in by_item.items():
        if not critic_ok:  # an untrusted critic is listed, never counted: not for a problem, not for a split
            notes += [{"item": item, "by": ["critic"], "acted_on": False, "why": "the critic failed its plan questions"} for r in rows if r["judge"] == "critic" and not r["ok"]]
            rows = [r for r in rows if r["judge"] != "critic"]
        bad = [r for r in rows if not r["ok"]]
        good = [r for r in rows if r["ok"]]
        if any(r["judge"] in trusted for r in bad):
            stand.append({"item": item, "by": sorted({r["judge"] for r in bad}), "detail": [r.get("detail") for r in bad]})
        elif len({r["judge"] for r in bad}) >= 2:
            stand.append({"item": item, "by": sorted({r["judge"] for r in bad}), "detail": [r.get("detail") for r in bad]})
        elif bad and good:
            ask.append({"item": item, "for": sorted({r["judge"] for r in good}), "against": sorted({r["judge"] for r in bad})})
        elif bad:
            notes.append({"item": item, "by": sorted({r["judge"] for r in bad}), "acted_on": False, "why": "a single weaker judge"})
    return {"problems": stand, "ask_person": ask, "notes": notes, "passed": not stand}
