from __future__ import annotations

import platform
import shlex
import time
from pathlib import Path

from coproducer import call
from coproducer.renderwatch import run_watching
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def _command(exe: str, folder: str, out_dir: str) -> list | str:
    line = '"%s" /R /Ewav /O"%s" /F"%s"' % (exe, out_dir, folder)
    return line if platform.system() == "Windows" else shlex.split(line)


def _blocked(projects: list) -> list:
    """Projects that use a plugin this FL edition has only as a trial (service fl_not_owned): FL would stop on a dialog."""
    owned_not = get_service("fl_not_owned") or []
    if not owned_not:
        return []
    out = []
    for p in projects:
        chk = call("check_project_health", project=str(p), not_owned=list(owned_not))
        if chk.ok and not chk.value["render_safe"]:
            out.append(p.name)
    return out


def render_folder_via_cli(folder: str, out_dir: str, timeout_s: int = 1800, stall_s: int = 300) -> Result:
    """Render every .flp project in a sandbox folder to WAV in one FL Studio launch (command line /R /Ewav /O /F). One file per project, named after it.
    Used for solo renders of each part. Refuses projects that use a plugin listed in config fl.not_owned (FL shows a trial dialog and waits), and
    stops FL when no WAV appears or grows for stall_s seconds (a dialog). Refuses while FL is running. Needs service fl_exe.
    Errors: E_SANDBOX_VIOLATION, E_UNSUPPORTED_API, E_NOT_FOUND, E_BLOCKED_BY_DIALOG, E_PENDING_HUMAN (FL running), E_TIMEOUT, E_IO, E_NOT_VERIFIED."""
    exe, root = get_service("fl_exe"), str(get_service("sandbox_root"))
    for p in (folder, out_dir):
        chk = call("check_sandbox_path", path=p, sandbox_root=root)
        if not chk.ok:
            return chk
    projects = sorted(Path(folder).glob("*.flp")) if Path(folder).is_dir() else []
    if not exe or not projects:
        return fail("E_UNSUPPORTED_API" if not exe else "E_NOT_FOUND", "need a configured FL executable and a folder with .flp projects")
    blocked = _blocked(projects)
    if blocked:
        return fail("E_BLOCKED_BY_DIALOG", "these projects use a plugin this FL edition does not own and FL would wait on a trial dialog: %s" % blocked)
    procs = get_service("procs")
    running = procs.fl_count() if procs else 0
    if running:
        return fail("E_PENDING_HUMAN", "FL Studio is running (or its state could not be read): a command-line render would hand the job to it and write "
                    "nothing. Close FL first, or use render_with_restart, which asks before closing it.", fl_processes=running)
    folder, out_dir = str(Path(folder).resolve()), str(Path(out_dir).resolve())
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    began = time.time()
    try:
        done = run_watching(_command(exe, folder, out_dir), out_dir, timeout_s, stall_s)
    except OSError as e:
        return fail("E_IO", "render did not start: %s" % e, retryable=True)
    if done["returncode"] is None:
        why = "no WAV appeared or grew for %d s: FL is probably showing a dialog" % stall_s if done["stalled"] else "timed out after %d s" % timeout_s
        return fail("E_TIMEOUT", "render stopped, %s" % why, retryable=True, seconds=done["seconds"])
    rows = [{"project": p.name, "wav": str(Path(out_dir) / (p.stem + ".wav"))} for p in projects]
    for r in rows:
        w = Path(r["wav"])
        r["written"] = w.is_file() and w.stat().st_mtime >= began - 1.0
        q = call("detect_silence", path=r["wav"]).value if r["written"] else {}
        r["silent_fraction"] = float(q.get("silent_fraction", 1.0))   # a sparse part (a harp run each bar) is mostly silent and still a sound
        r["mostly_silent"], r["silent"] = bool(q.get("mostly_silent", True)), bool(float(r["silent_fraction"]) >= 0.999)
    if done["returncode"] != 0 or not any(r["written"] for r in rows):
        return fail("E_IO", "FL exited with %d and wrote no new WAV in %s" % (done["returncode"], out_dir))
    missing = [r["project"] for r in rows if not r["written"]]
    return ok({"rendered": rows, "missing": missing}, verified=not missing)
