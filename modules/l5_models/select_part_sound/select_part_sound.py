from __future__ import annotations

import json
from pathlib import Path

from coproducer import call, soundbrief, soundpick
from coproducer.result import Result, fail, ok
from coproducer.services import get_service

MAKE_KEYS = ("start_s", "end_s", "rounds", "key_pc", "template_project", "presets_dir", "direction")


def _hear(p: dict, k: int, ctx: dict) -> dict:
    """Play one library preset on the audition notes and compare it with the original's part (a row with an error when it failed)."""
    row = {"source": "library", "preset": p["name"], "path": p["rel"]}
    r = call("render_serum_sound", notes=ctx["notes"], out_path=str(Path(ctx["out_dir"]) / ("%s_lib%d.wav" % (ctx["slug"], k))),
             preset_path=p["path"], bpm=120, **ctx["template"])
    if not r.ok:
        return {**row, "error": r.error.code}
    try:
        x, rate = soundbrief.load_slice(r.value["wav"])
        cmp = soundbrief.compare(ctx["sound"], soundbrief.describe(x, rate), ctx["role"])
    except ValueError as e:
        return {**row, "error": "E_ARG", "message": str(e)}
    return {**row, "wav": r.value["wav"], "state": r.value["state"], "rms_db": r.value["rms_db"], "match": cmp["match"],
            "distance": soundbrief.distance(cmp["differences"]), "adjust": cmp["adjust"]}


def _made(stem: str, role: str, name: str, subfolder: str, ctx: dict, opt: dict) -> dict:
    """A sound made for the part (match_part_sound), as a candidate row."""
    g = call("match_part_sound", stem=stem, role=role, name=name, out_dir=ctx["out_dir"], subfolder=subfolder,
             options={**{k: opt[k] for k in MAKE_KEYS if k in opt}, "notes": ctx["notes"]})
    if not g.ok:
        return {"source": "made", "preset": name, "error": g.error.code}
    best = next(r for r in g.value["rounds"] if r.get("round") == g.value["best"])
    return {"source": "made", "preset": name, "path": g.value["preset"], "wav": g.value["wav"], "state": g.value["state"],
            "rms_db": best["rms_db"], "match": g.value["match"], "distance": best["distance"], "adjust": best["adjust"]}


def select_part_sound(stem: str, role: str, name: str, song: str, out_dir: str, subfolder: str, library_dir: str, options: dict | None = None) -> Result:
    """This song's sound for one part (no default sound for any part): measure the original's part, play options.candidates (default 6)
    library presets no other song or part has taken (soundpick), add a sound made for it (match_part_sound, unless options.make is false),
    keep the nearest and write it to the sound history. Options: candidates, make, seed, key_pc, notes, start_s, end_s, rounds,
    template_project, presets_dir, direction, history_file (default sandbox\\sound_history.json).

    Errors: E_SANDBOX_VIOLATION, E_NOT_FOUND (no notes in the stem, or no candidate sounded), E_MODEL."""
    opt, root = options or {}, str(get_service("sandbox_root"))
    hist_path = opt.get("history_file") or str(Path(root) / "sound_history.json")
    for p in (out_dir, hist_path):
        chk = call("check_sandbox_path", path=p, sandbox_root=root)
        if not chk.ok:
            return chk
    m = call("measure_part_sound", path=stem, start_s=float(opt.get("start_s", 0.0)), end_s=float(opt.get("end_s", 0.0)), role=role, name=name)
    if not m.ok:
        return m
    sound = soundbrief.blend(m.value["sound"], opt["direction"]) if opt.get("direction") else m.value["sound"]
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    ctx = {"sound": sound, "role": role, "out_dir": out_dir, "slug": soundpick.slug(name),
           "notes": opt.get("notes") or soundpick.audition(sound, role, int(opt.get("key_pc", 0))),
           "template": {"template_project": opt["template_project"]} if opt.get("template_project") else {}}
    used = soundpick.taken(soundpick.load_history(hist_path), song, role)
    picks = soundpick.candidates(soundpick.catalog(library_dir, role), song, role, used, int(opt.get("candidates", 6)), str(opt.get("seed", "")))
    rows = [_hear(p, k, ctx) for k, p in enumerate(picks, 1)]
    if opt.get("make", True):
        rows.append(_made(stem, role, name, subfolder, ctx, opt))
    heard = [r for r in rows if "distance" in r and r["rms_db"] > -60.0]
    table = [{k: r.get(k) for k in ("source", "preset", "path", "distance", "match", "error")} for r in rows]
    if not heard:
        return fail("E_NOT_FOUND", "no candidate sound played for %s" % role, candidates=table)
    best = min(heard, key=lambda r: r["distance"])
    soundpick.record(hist_path, song, role, best)
    (Path(out_dir) / ("%s_choice.json" % ctx["slug"])).write_text(json.dumps({"sound": sound, "candidates": rows}, indent=1, default=str), encoding="utf-8")
    return ok({"state": best["state"], "wav": best["wav"], "preset": best["preset"], "path": best["path"], "source": best["source"],
               "distance": best["distance"], "match": best["match"], "left": best["adjust"], "words": sound.get("words", []),
               "candidates": table, "taken_elsewhere": len(used)}, verified=best["rms_db"] > -60.0)
