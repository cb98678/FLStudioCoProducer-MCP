from __future__ import annotations

import json
from pathlib import Path

from coproducer import call, soundbrief
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def _notes(sound: dict, role: str, key_pc: int) -> list:
    """The measured notes to audition on, or for a chord part (no single pitch) the key's root, fifth and octave four times."""
    if sound.get("audition_notes"):
        return sound["audition_notes"]
    root = (36 if role in ("sub", "bass") else 60) + key_pc
    return [{"pitch": p, "start": 2.0 * k, "duration": 1.0, "velocity": 100} for k in range(4) for p in ((root,) if root < 48 else (root, root + 7, root + 12))]


def _round(spec: dict, k: int, ctx: dict) -> dict:
    """Generate, render and compare one spec. Returns the round's row (with an error when a step failed)."""
    g = call("generate_serum_preset", spec=spec, subfolder=ctx["subfolder"], **ctx["presets"])
    if not g.ok:
        return {"round": k, "error": g.error.code, "message": g.error.message}
    out = str(Path(ctx["out_dir"]) / ("%s_r%d.wav" % (ctx["slug"], k)))
    r = call("render_serum_sound", notes=ctx["notes"], out_path=out, preset_path=g.value["path"], bpm=120, **ctx["template"])
    if not r.ok:
        return {"round": k, "error": r.error.code, "message": r.error.message}
    x, rate = soundbrief.load_slice(r.value["wav"])
    cmp = soundbrief.compare(ctx["sound"], soundbrief.describe(x, rate), ctx["role"])
    return {"round": k, "spec": spec, "preset": g.value["path"], "wav": r.value["wav"], "state": r.value["state"], "rms_db": r.value["rms_db"],
            "differences": cmp["differences"], "adjust": cmp["adjust"], "match": cmp["match"], "distance": soundbrief.distance(cmp["differences"])}


def match_part_sound(stem: str, role: str, name: str, out_dir: str, subfolder: str, options: dict | None = None) -> Result:
    """Measure the original's part on its stem (measure_part_sound), generate a Serum 2 preset from the reading, play it headless on the
    measured notes, compare and revise, up to options.rounds (default 3); keeps the round nearest the original and rewrites the preset
    from its spec. The state goes to build_remix_project's serum_states. Options: start_s, end_s, rounds, key_pc, notes, template_project,
    presets_dir, direction (a measured demo sound: its envelope and width on the original's tone, soundbrief.blend).

    Errors: E_SANDBOX_VIOLATION, E_NOT_FOUND (no notes in the stem), E_MODEL, and the first failing step's error when no round finished.
    """
    opt = options or {}
    chk = call("check_sandbox_path", path=out_dir, sandbox_root=str(get_service("sandbox_root")))
    if not chk.ok:
        return chk
    m = call("measure_part_sound", path=stem, start_s=float(opt.get("start_s", 0.0)), end_s=float(opt.get("end_s", 0.0)), role=role, name=name)
    if not m.ok:
        return m
    sound, spec = m.value["sound"], m.value["starting_point"]["spec"]
    if opt.get("direction"):  # a demo instrument's envelope and space on the original's tone (variety sound choice)
        sound = soundbrief.blend(sound, opt["direction"])
        spec = soundbrief.starting_point(sound, role, name)["spec"]
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    ctx = {"sound": sound, "role": role, "subfolder": subfolder, "out_dir": out_dir, "slug": "".join(c if c.isalnum() else "_" for c in name).strip("_"),
           "notes": opt.get("notes") or _notes(sound, role, int(opt.get("key_pc", 0))),
           "presets": {"presets_dir": opt["presets_dir"]} if opt.get("presets_dir") else {},
           "template": {"template_project": opt["template_project"]} if opt.get("template_project") else {}}
    rows = []
    for k in range(1, int(opt.get("rounds", 3)) + 1):
        row = _round(spec, k, ctx)
        rows.append(row)
        worse = len(rows) > 1 and "error" not in row and row["distance"] >= min(r["distance"] for r in rows[:-1] if "error" not in r)
        if "error" in row or row["match"] or worse:             # a round no nearer the original than the best so far ends the search
            break
        spec, row["changes"] = soundbrief.revise(spec, row, sound, role)
    done = [r for r in rows if "error" not in r]
    if not done:
        return fail(rows[-1]["error"], rows[-1]["message"], rounds=rows)
    best = min(done, key=lambda r: r["distance"])
    if best is not done[-1]:
        call("generate_serum_preset", spec=best["spec"], subfolder=subfolder, **ctx["presets"])   # the library keeps the best round's preset
    (Path(out_dir) / ("%s_match.json" % ctx["slug"])).write_text(json.dumps({"sound": sound, "rounds": rows}, indent=1, default=str), encoding="utf-8")
    return ok({"state": best["state"], "wav": best["wav"], "preset": best["preset"], "best": best["round"], "match": best["match"],
               "words": sound.get("words", []), "rounds": [{k: v for k, v in r.items() if k != "spec"} for r in rows]}, verified=best["rms_db"] > -60.0)
