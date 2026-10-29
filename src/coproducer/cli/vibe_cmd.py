"""The first full vibe loop on a real machine: generate a clip, bring it into the open sandbox project, render, listen.

Every step is an ordinary module call, so each one is checked on its own. The run stops at the first step that fails.
"""
from __future__ import annotations

import time
from pathlib import Path

from . import polish_cmd, probe_cmd as p

SILENT_LUFS = -60.0


def _step(out: dict, name: str, r, **extra) -> bool:
    out["steps"][name] = {"ok": r.ok, **({"error": "%s %s" % (r.error.code, r.error.message)} if not r.ok else {}), **extra}
    return r.ok


def _open_matches(call, project: Path) -> str | None:
    """None when the window title names the project file, else a sentence saying what is open."""
    ready = call("check_desktop_ready")
    if not ready.ok:
        return "%s %s" % (ready.error.code, ready.error.message)
    if project.stem.lower() not in ready.value["title"].lower():
        return "FL shows %r but the run is for %s; open that sandbox project first" % (ready.value["title"], project.name)
    return None


def _bring_in(call, out: dict, src: str, track: int) -> bool:
    """Import the clip, place it on a playlist track, switch to song mode and save, so the next render holds it."""
    return (_step(out, "import", call("import_audio_clip_gui", path=src))
            and _step(out, "place", call("add_audio_clip_to_playlist_gui", track=track))
            and _step(out, "song_mode", call("ensure_loop_mode", song=True))
            and _step(out, "save", call("save_sandbox_project", project=str(out["project"]))))


def _audible(out: dict, src_report: dict, listened: dict) -> None:
    """Record how loud the generated clip and the render are, and whether the render is more than silence."""
    heard, source = p._lufs(listened.get("report", {})), p._lufs(src_report)
    out["steps"]["audible"] = {"ok": heard is not None and heard > SILENT_LUFS, "render_lufs": heard, "clip_lufs": source}


def vibe(call, project: Path, work: Path, prompt: str, bpm: float = 128.0, duration_s: float = 10.0, track: int = 1,
         adjust: bool = False, keep: bool = False) -> dict:
    """Generate a clip, import it into the open sandbox project on a playlist track, save, render with FL restarted, and listen to the result.

    With adjust, the brain's gain and EQ proposals are applied and checked against a second render (polish); every change is put back unless all its checks passed (the sandbox copy then keeps the better mix) or keep is set.
    """
    project, work = Path(project), Path(work)
    out: dict = {"steps": {}, "project": str(project), "prompt": prompt, "track": track}
    t0 = time.monotonic()
    wrong = _open_matches(call, project)
    if wrong:
        out["steps"]["project_open"] = {"ok": False, "error": wrong}
        return {**out, "passed": False}
    gen = call("generate_audio", prompt=prompt, out_dir=str(work / "gen"), duration_s=duration_s, bpm=bpm)
    if not _step(out, "generate", gen, seconds=round(time.monotonic() - t0, 1)):
        return {**out, "passed": False}
    src = gen.value["paths"][0]
    out["clip"] = src
    src_rep = call("build_measure_report", path=src)
    _step(out, "measure_clip", src_rep)
    if not _bring_in(call, out, src, track):
        return {**out, "passed": False}
    heard = polish_cmd.polish(call, project, work / "polish", bpm, keep, keep_if_heard=True) if adjust else p.listen(call, project, work / "listen", bpm)
    out["steps"].update(heard["steps"])
    out["eq_checks"] = heard.get("eq_checks")
    for k in ("audio", "report", "listener_notes", "proposals", "plan", "loudness", "kept"):
        if k in heard:
            out[k] = heard[k]
    _audible(out, src_rep.value if src_rep.ok else {}, heard)
    out["passed"] = all(v["ok"] for v in out["steps"].values()) and (not adjust or bool(heard.get("passed")))
    return out
