"""The global halt key: one key combination, anywhere in Windows, stops every run and every input action.

`coproducer halt --key` runs the listener (leave its window open). Pressing Ctrl+Alt+F12 writes the global HALT file, `runs/HALT`.
Every input primitive and the orchestrator check that file before each action, so the action in flight finishes and nothing after it runs.
A person clears it with `coproducer halt --clear`. Without the Windows API (Linux, tests) only the file functions work.
"""
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

MOD_ALT, MOD_CONTROL, MOD_NOREPEAT = 0x0001, 0x0002, 0x4000
VK_F12 = 0x7B
WM_HOTKEY = 0x0312
DEFAULT_KEYS = "Ctrl+Alt+F12"


def global_halt_file(home: Path | str, runs: str = "runs") -> Path:
    return Path(home) / runs / "HALT"


def trip(home: Path | str, why: str = "halt key pressed") -> Path:
    f = global_halt_file(home)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("%s at %s" % (why, time.strftime("%Y-%m-%d %H:%M:%S")), encoding="utf-8")
    return f


def clear(home: Path | str) -> bool:
    """Remove the global HALT file and every run's HALT file. True when something was removed."""
    removed = False
    root = Path(home) / "runs"
    for f in [root / "HALT", *root.glob("*/HALT")] if root.is_dir() else []:
        try:
            f.unlink()
            removed = True
        except FileNotFoundError:
            pass
    return removed


def listen(home: Path | str, stop: threading.Event | None = None, on_trip=None, say=print) -> int:
    """Register Ctrl+Alt+F12 and block until `stop` is set (or forever). Returns how many times the key was pressed."""
    if sys.platform != "win32":
        raise OSError("the halt key needs Windows")
    import ctypes
    import ctypes.wintypes as wt
    user32 = ctypes.windll.user32
    if not user32.RegisterHotKey(None, 1, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, VK_F12):
        raise OSError("%s is already taken by another program" % DEFAULT_KEYS)
    pressed = 0
    msg = wt.MSG()
    say("halt key ready: %s stops all runs. Watching; close this window to stop watching." % DEFAULT_KEYS)
    try:
        while not (stop and stop.is_set()):
            if user32.PeekMessageW(ctypes.byref(msg), None, WM_HOTKEY, WM_HOTKEY, 1):
                pressed += 1
                f = trip(home)
                try:
                    ctypes.windll.kernel32.Beep(880, 200)
                except OSError:
                    pass
                say("HALT: wrote %s. Clear it with: coproducer halt --clear" % f)
                if on_trip:
                    on_trip(f)
            else:
                time.sleep(0.02)
    finally:
        user32.UnregisterHotKey(None, 1)
    return pressed
