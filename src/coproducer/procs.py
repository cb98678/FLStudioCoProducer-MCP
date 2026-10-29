"""Start and stop FL Studio as a process. Windows only; the modules reach it through the "procs" service.

FL Studio runs one copy at a time: its command line (/R render) hands the job to a running copy and exits at once,
so a render has to run with FL closed (measured 2026-10-18). Closing is graceful (taskkill without /F), which never discards work:
an unsaved project makes FL ask first, and the caller sees that FL did not close.
"""
from __future__ import annotations

import subprocess
import time
from pathlib import Path


class Procs:
    def fl_count(self) -> int:
        """How many FL64.exe processes are running, or -1 when tasklist could not answer. Callers test the count for truth, so an unknown state
        counts as running: a render or a launch never goes ahead on a guess that FL is closed."""
        try:
            done = subprocess.run(["tasklist", "/FI", "IMAGENAME eq FL64.exe", "/FO", "CSV", "/NH"], capture_output=True, text=True, timeout=15, check=False)
        except (subprocess.SubprocessError, OSError):
            return -1
        if done.returncode != 0:
            return -1
        return sum(1 for line in done.stdout.splitlines() if "fl64.exe" in line.lower())

    def close_fl(self, timeout_s: float = 30.0) -> bool:
        """Ask FL to close and wait until it has. False when it is still running (for example a Save changes dialog is open)."""
        try:
            subprocess.run(["taskkill", "/IM", "FL64.exe"], capture_output=True, timeout=15, check=False)
        except (subprocess.SubprocessError, OSError):
            return False
        end = time.monotonic() + timeout_s
        while time.monotonic() < end:
            if self.fl_count() == 0:
                return True
            time.sleep(0.5)
        return self.fl_count() == 0

    def launch(self, exe: str, project: str) -> None:
        """Start FL with a project and return at once.

        The project path is made absolute first: FL keeps the path it was given, and a relative one
        makes plain Save fail with "Could not save to the file" (measured 2026-10-19).
        """
        flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        subprocess.Popen([exe, str(Path(project).resolve())], creationflags=flags, close_fds=True)
