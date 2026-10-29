from __future__ import annotations

import time
from pathlib import Path

from coproducer import call
from coproducer.result import Result, fail, ok
from coproducer.services import get_service

NAMES = (("vocals", "vocals"), ("drums", "drums"), ("bass", "bass"), ("instruments", "other"))   # FL's stem -> the intake's file name


def _open(project: str, wait_s: float = 120.0) -> Result:
    """Start FL on the project when FL is closed; open it as a sandbox copy when FL runs (that stops at a Save changes question)."""
    procs, exe = get_service("procs"), get_service("fl_exe")
    if procs is None or not exe or procs.fl_count():
        return call("open_project_copy", path=project)
    procs.launch(exe, project)
    end, name = time.monotonic() + wait_s, Path(project).name.lower()
    while time.monotonic() < end:
        r = call("check_desktop_ready")
        if r.ok and name in r.value["title"].lower():
            time.sleep(3.0)                                       # the project's clips are still loading when the title shows
            return ok(True)
        time.sleep(2.0)
    return fail("E_TIMEOUT", "FL did not open %s within %d s" % (name, wait_s))


def _finished(paths: list, timeout_s: float) -> bool:
    """Every stem file exists and has kept its size for 3 s (FL is unresponsive while it separates, then writes the four files)."""
    end, last = time.monotonic() + timeout_s, None
    while time.monotonic() < end:
        now = [Path(p).stat().st_size if Path(p).is_file() else -1 for p in paths]
        if min(now) > 0 and now == last:
            return True
        last = now
        time.sleep(3.0)
    return False


def extract_stems_gui(path: str, out_dir: str, template: str = "", timeout_s: float = 900.0) -> Result:
    """Split a song into vocals, drums, bass and other with FL Studio's own "Extract stems from sample" (playlist clip menu), not a local model.

    prepare_stems_project writes a sandbox project with the song on playlist track 1, FL opens it (started when closed), the recipe
    extract_stems_gui runs the menu and the Extract button, and the four stems FL writes are copied to out_dir as vocals.wav, drums.wav,
    bass.wav and other.wav (FL's Instruments). Stems already extracted for this song are reused. Errors: E_SANDBOX_VIOLATION, E_NOT_FOUND,
    E_TIMEOUT, E_GUI_MISMATCH, E_BLOCKED_BY_DIALOG, E_HALTED.
    """
    dst = call("check_sandbox_path", path=out_dir, sandbox_root=str(get_service("sandbox_root")))
    if not dst.ok:
        return dst
    prep = call("prepare_stems_project", song=path, out_project=str(Path(dst.value["resolved"]) / "fl_stems_bench.flp"), template=template)
    if not prep.ok:
        return prep
    exp = prep.value["expected"]
    if not prep.value["ready"]:
        for step in (lambda: _open(prep.value["project"]), lambda: call("run_gui_recipe", name="extract_stems_gui", params={})):
            got = step()
            if not got.ok:
                return got
        if not _finished(list(exp.values()), timeout_s):
            return fail("E_TIMEOUT", "FL's stems did not all appear within %d s" % timeout_s, expected=exp)
    stems = {}
    for part, name in NAMES:
        target = Path(dst.value["resolved"]) / (name + ".wav")
        target.write_bytes(Path(exp[part]).read_bytes())
        stems[name] = str(target)
    return ok({"stems": stems, "project": prep.value["project"], "extracted": not prep.value["ready"], "fl_files": exp})
