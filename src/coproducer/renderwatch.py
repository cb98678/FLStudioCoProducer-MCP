"""Run FL's command-line render and stop it when it stalls.

A modal dialog (a trial plugin, a missing sample, a crash report) stops FL before it renders, and FL then waits for a click that never comes. On
2026-10-25 a trial-plugin warning held a folder render until its 40-minute timeout. This runner watches the output folder and stops FL when no WAV
has appeared or grown for stall_s seconds.
"""
from __future__ import annotations

import subprocess
import time
from pathlib import Path


def _progress(out_dir: str) -> tuple:
    return tuple(sorted((p.name, p.stat().st_size, int(p.stat().st_mtime)) for p in Path(out_dir).glob("*.wav")))


def run_watching(cmd, out_dir: str, timeout_s: float, stall_s: float, poll_s: float = 2.0) -> dict:
    """Run cmd; return {"returncode", "stalled", "timed_out", "seconds"}. The process is killed on a stall or the timeout."""
    began = time.time()
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    seen, last = _progress(out_dir), began
    while proc.poll() is None:
        time.sleep(poll_s)
        now, cur = time.time(), _progress(out_dir)
        if cur != seen:
            seen, last = cur, now
        if now - began > timeout_s or now - last > stall_s:
            proc.kill()
            proc.wait()
            return {"returncode": None, "stalled": now - last > stall_s, "timed_out": now - began > timeout_s, "seconds": round(now - began, 1)}
    return {"returncode": proc.returncode, "stalled": False, "timed_out": False, "seconds": round(time.time() - began, 1)}
