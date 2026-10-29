"""coproducer calibrate: record click anchors as window pixels. Windows only; the person hovers, the tool reads the cursor."""
from __future__ import annotations

import sys
from pathlib import Path

from ..config import load_config, render_config


def cursor_in_window(desktop=None) -> tuple:
    """(x, y) of the mouse relative to the FL window's top-left corner."""
    import ctypes
    import ctypes.wintypes
    pt = ctypes.wintypes.POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    from ..desktop_win import WinDesktop
    win = (desktop or WinDesktop()).find_window()
    if win is None:
        raise RuntimeError("FL Studio window not found")
    return pt.x - win["left"], pt.y - win["top"]


def save_anchor(home: Path, name: str, xy: tuple) -> str:
    cfg = load_config(home)
    cfg["anchors"][name] = "%d,%d" % xy
    (home / "config.toml").write_text(render_config(cfg), encoding="utf-8", newline="\n")
    return cfg["anchors"][name]


def calibrate(home: Path, names: list, read=input, cursor=cursor_in_window, out=print) -> list:
    done = []
    for name in names:
        read("Hover the mouse over '%s' in FL Studio, then press Enter here: " % name)
        done.append((name, save_anchor(home, name, cursor())))
        out("saved %s = %s" % done[-1])
    return done


def available() -> bool:
    return sys.platform == "win32"
