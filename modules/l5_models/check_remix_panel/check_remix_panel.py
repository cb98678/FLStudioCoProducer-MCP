from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from coproducer import call, dsp, panel, stylepack, tonal
from coproducer.result import Result, fail, ok
from coproducer.services import get_service

VOICE_LU = -20.0  # a vocal stem this far under the excerpt counts as buried; a first guess, to calibrate on mixes the person approves


def _excerpt(src: str, start_s: float, seconds: float, dst: Path) -> str | None:
    ff = shutil.which("ffmpeg")
    if not ff:
        return None
    done = subprocess.run([ff, "-y", "-hide_banner", "-loglevel", "error", "-ss", "%.3f" % start_s, "-t", "%.3f" % seconds, "-i", src, str(dst)],
                          capture_output=True, check=False)
    return str(dst) if done.returncode == 0 and dst.is_file() and dst.stat().st_size > 100_000 else None  # an excerpt past the end is empty


def check_remix_panel(path: str, plan_file: str, targets_file: str, mixdown: str = "", references: list | None = None, options: dict | None = None) -> Result:
    """The evaluation panel on a mastered remix and its plan: every targets limit on the master, length against the plan, section contrast on the
    mixdown (sections from the plan, window from the targets' [contrast]), the critic on 16 s of the first drop graded on yes-or-no questions the style answers (trusted at 0.75 or
    better), with references whether it sounds closer to them than options.original, with options.profile its tonal balance. critic false skips the critic.
    panel.verdict lists the problems that stand, what to ask the person, and notes it does not act on. A1: it loads a 16 GB model.
    Errors: E_NOT_FOUND, E_ARG (bad plan or targets).
    """
    opt = options or {}
    critic, original = opt.get("critic", True) is not False, opt.get("original", "")
    for p in (path, plan_file, targets_file):
        if not Path(p).is_file():
            return fail("E_NOT_FOUND", "no file at %s" % Path(p).name)
    plan = json.loads(Path(plan_file).read_text(encoding="utf-8"))
    style = stylepack.load(plan["style"]) if plan.get("style") else None
    rep, lim = call("build_measure_report", path=path), call("load_targets_file", path=targets_file)
    if not rep.ok or not lim.ok:
        return rep if not rep.ok else lim
    rows = call("check_report_limits", report=rep.value, limits=lim.value["limits"])
    findings = [{"judge": "dsp", "item": r["label"], "ok": r["within"], "detail": r} for r in (rows.value["rows"] if rows.ok else [])]
    bpm, bars = float(plan["bpm"]), plan["sections"][-1]["end"]
    want, got = bars * 240 / bpm, rep.value.get("silence", {}).get("duration_s")
    findings.append({"judge": "dsp", "item": "length against the plan", "ok": got is not None and -2.0 <= got - want < 8.0,
                     "detail": {"bars": bars, "expected_s": round(want, 2), "render_s": got}})
    names = [n.title() if sum(1 for t in plan["sections"] if t["name"] == n) == 1 else "%s %d" % (n.title(), k) for n, k in _numbered(plan["sections"])]
    secs = [{"name": nm, "start_bar": t["start"] + 1, "end_bar": t["end"] + 1} for nm, t in zip(names, plan["sections"])]
    sec = call("measure_section_levels", path=mixdown or path, sections=secs, bpm=bpm)   # without bpm (or a project) it measured nothing: until 2026-10-28
    dc = call("measure_dc_offset", path=mixdown) if mixdown else None
    if dc is not None and dc.ok:  # the master removes DC, so an offset in the mixdown points at a plugin state in the project: a recipe to fix
        findings.append({"judge": "dsp", "item": "held dc offset in the mixdown", "ok": dc.value["held_dbfs"] <= -60.0, "detail": dc.value})
    span = lim.value.get("contrast", {}).get("drop_over_build_lu") or {"min": 3.0}
    for c in (sec.value["contrast"] if sec.ok else []):
        if c.get("over_before_lu") is not None and (c.get("before") or "").lower().startswith("build"):  # a hook after a verse is not a build drop
            inside = span.get("min", -99) <= c["over_before_lu"] <= span.get("max", 99)
            findings.append({"judge": "dsp", "item": "contrast %s" % c["drop"], "ok": inside, "detail": c})
    if opt.get("profile") and Path(opt["profile"]).is_file():  # tonal balance against the person's references: worst band beyond their spread
        prof = json.loads(Path(opt["profile"]).read_text(encoding="utf-8"))["tonal"]
        dev = tonal.deviation(tonal.band_levels(*dsp.load_audio(path)), prof)
        tol = float(lim.value.get("spectrum", {}).get("band_tolerance_db", 3.0))
        findings.append({"judge": "dsp", "item": "tonal balance against the references", "ok": abs(dev["worst_db"]) <= tol, "detail": dev})
    graded = _judge_drop(path, plan, style if critic else None, bpm, findings)
    if references:
        sim = call("compare_to_references_ml", path=path, references=list(references), **({"baseline": original} if original else {}))
        if sim.ok:
            findings.append({"judge": "similarity", "item": "sounds like the references", "ok": bool(sim.value.get("closer_than_baseline", True)), "detail": sim.value})
    out = panel.verdict(findings, graded)
    out["ask_person"] += _flat_drops(sec.value["contrast"] if sec.ok else [])
    return ok({**out, "critic": graded, "findings": findings}, verified=rows.ok and sec.ok)


def _flat_drops(rows: list, min_lu: float = 1.0) -> list:
    """Drops that sit under min_lu over the section before them when that is not a build (a verse or groove): a form can mean it (filters
    instead of drops), so the person is asked, it is not a problem. Seen 2026-10-28: two house remixes with drops 0.1 to 0.6 LU over the grooves."""
    flat = [c for c in rows if c.get("over_before_lu") is not None and c["over_before_lu"] < min_lu and not (c.get("before") or "").lower().startswith("build")]
    return [{"item": "drops barely above the section before them", "for": [], "against": ["dsp"],
             "detail": [{k: c.get(k) for k in ("drop", "before", "over_before_lu")} for c in flat]}] if flat else []


def _numbered(sections: list) -> list:
    """(kind, occurrence number) per section, as the build numbers its markers (Drop 1, Drop 2)."""
    seen: dict = {}
    out = []
    for t in sections:
        seen[t["name"]] = seen.get(t["name"], 0) + 1
        out.append((t["name"], seen[t["name"]]))
    return out


def _vocal_lu(clip: str) -> float | None:
    """Loudness of the separated vocal of an excerpt against the excerpt itself (LU), by Mel-Band RoFormer, or None when the model is missing."""
    m = (get_service("model_files") or {}).get("roformer_vocals", {})
    got = call("run_model_op", model="roformer", op="vocals", timeout_s=900, args={"path": clip, "out_dir": str(Path(clip).parent / "panel_sep"),
               "model_dir": m.get("model_dir", ""), "model": m.get("model", "vocals_mel_band_roformer.ckpt"), "sha256": m.get("sha256", "")})
    if not got.ok:
        return None
    v, mix = call("measure_integrated_loudness", path=got.value["vocals"]), call("measure_integrated_loudness", path=clip)
    return round(v.value["lufs"] - mix.value["lufs"], 1) if v.ok and mix.ok else None


def _judge_drop(path: str, plan: dict, style: dict | None, bpm: float, findings: list) -> dict | None:
    """16 s of the first drop: the separation judge measures the voice where the plan put chops; then, with a style, the critic answers the plan
    questions, graded against the known answers (the voice by the separation when it ran), and its answers are added as findings."""
    drop = next((s for s in plan["sections"] if s["name"] == "drop"), None)
    clip = _excerpt(path, drop["start"] * 240 / bpm + 1.0, 16.0, Path(path).with_name("panel_excerpt.wav")) if drop else None
    if not clip:
        return None
    planned = any(drop["start"] <= e[0] < drop["end"] for e in plan.get("chop_events", []))
    voice = _vocal_lu(clip)
    if voice is not None:
        findings.append({"judge": "separation", "item": "voice audible in the first drop", "ok": not planned or voice >= VOICE_LU,
                         "detail": {"vocal_minus_mix_lu": voice, "planned": planned}})
    if style is None:
        return None
    qs = panel.plan_questions(style)
    has_voice = (voice >= VOICE_LU) if voice is not None else planned
    for q in qs:  # the voice question may be asked the inverse way (yes means instrumental); plan and truth are turned to match
        flip = q.get("yes_means_voice", True) is False
        q["plan"] = (planned != flip) if q["expect"] is None else q["expect"]
        if q["expect"] is None:
            q["expect"] = has_voice != flip
    answers = []
    for q in qs:
        got = call("run_model_op", model="flamingo", op="critique", args={"path": clip, "prompt": q["q"], "max_new_tokens": 60}, timeout_s=900)
        answers.append({**q, "answer": got.value["text"] if got.ok else "", "error": None if got.ok else got.error.code})
    findings += [{"judge": "critic", "item": a["item"], "ok": panel.yes_no(a["answer"]) == a["plan"], "detail": a["answer"][:200]}
                 for a in answers if panel.yes_no(a["answer"]) is not None]
    return panel.grade_critic(answers)
