from __future__ import annotations

import platform
import shlex
import time
from pathlib import Path

from coproducer import call
from coproducer.renderwatch import run_watching
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def _command(exe: str, project: str, out_dir: str) -> list | str:
    line = '"%s" /R /Ewav /O"%s" "%s"' % (exe, out_dir, project)
    return line if platform.system() == "Windows" else shlex.split(line)


def _newest_wav(out_dir: str, since: float):
    found = [p for p in Path(out_dir).glob("*.wav") if p.stat().st_mtime >= since - 1.0]
    return max(found, key=lambda p: p.stat().st_mtime) if found else None


def _not_owned_in(project: str) -> bool:
    owned_not = get_service("fl_not_owned") or []
    chk = call("check_project_health", project=project, not_owned=list(owned_not)) if owned_not else None
    return bool(chk and chk.ok and not chk.value["render_safe"])


def render_via_cli(project: str, out_dir: str, timeout_s: int = 600, stall_s: int = 300) -> Result:
    """Render a saved sandbox project to WAV with FL Studio's command line (/R /Ewav /O) and check the file is not silent.

    Refuses a project that uses a plugin listed in config fl.not_owned (FL would wait on a trial dialog) and stops FL when no WAV appears or grows
    for stall_s seconds. Refuses while FL is running (FL would take the job and write nothing; measured 2026-10-18). Needs service fl_exe.
    Errors: E_SANDBOX_VIOLATION, E_UNSUPPORTED_API, E_BLOCKED_BY_DIALOG, E_PENDING_HUMAN (FL running), E_TIMEOUT, E_IO, E_NOT_VERIFIED.
    """
    exe, root = get_service("fl_exe"), str(get_service("sandbox_root"))
    for p in (project, out_dir):
        chk = call("check_sandbox_path", path=p, sandbox_root=root)
        if not chk.ok:
            return chk
    if not exe or not Path(project).is_file():
        return fail("E_UNSUPPORTED_API" if not exe else "E_NOT_FOUND", "need a configured FL executable and a saved project file")
    if _not_owned_in(project):
        return fail("E_BLOCKED_BY_DIALOG", "the project uses a plugin this FL edition does not own; FL would wait on a trial dialog")
    procs = get_service("procs")
    running = procs.fl_count() if procs else 0
    if running:
        return fail("E_PENDING_HUMAN", "FL Studio is running (or its state could not be read): a command-line render would hand the job to it and write "
                    "nothing. Close FL first, or use render_with_restart, which asks before closing it.", fl_processes=running)
    project, out_dir = str(Path(project).resolve()), str(Path(out_dir).resolve())    # FL does not run in our folder, so a relative path breaks
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    began = time.time()
    try:
        done = run_watching(_command(exe, project, out_dir), out_dir, timeout_s, stall_s)
    except OSError as e:
        return fail("E_IO", "render did not start: %s" % e, retryable=True)
    if done["returncode"] is None:
        why = "no WAV appeared or grew for %d s: FL is probably showing a dialog" % stall_s if done["stalled"] else "timed out after %d s" % timeout_s
        return fail("E_TIMEOUT", "render stopped, %s" % why, retryable=True, seconds=done["seconds"])
    wav = _newest_wav(out_dir, began)
    if done["returncode"] != 0 or wav is None:
        return fail("E_IO", "FL exited with %d after %.1f s and wrote no new WAV in %s. FL may be showing an error window. exe: %s"
                    % (done["returncode"], time.time() - began, out_dir, exe))
    quiet = call("detect_silence", path=str(wav))
    if not quiet.ok or quiet.value["mostly_silent"]:
        return fail("E_NOT_VERIFIED", "the rendered file is empty or silent: %s" % wav.name)
    return ok({"path": str(wav), "bytes": wav.stat().st_size}, verified=True)
