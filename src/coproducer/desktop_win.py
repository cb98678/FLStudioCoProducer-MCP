"""Windows desktop backend for the L6 modules: Win32 through ctypes, screenshots with mss, input with pyautogui.

Written against the documented APIs (EnumWindows, GetWindowTextW, GetWindowRect, GetForegroundWindow, SetForegroundWindow,
GetWindowThreadProcessId, GetDpiForWindow; mss.grab; pyautogui click, moveTo, write, hotkey). It cannot run on Linux.
Gate 0 runs probes/probe_desktop.py on the real machine to prove each call reaches FL Studio's window.
Optional libraries are imported when first used, so importing this file is always safe.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes
import re
import sys
import time
from typing import Any


def _user32():
    return ctypes.windll.user32  # type: ignore[attr-defined]


def make_dpi_aware() -> None:
    """Report physical pixels, so screenshot and click coordinates agree at any display scale."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass


MAIN_TITLE = r"FL Studio \d{4}\s*$"    # "song.flp - FL Studio 2026" or "FL Studio 2026"; not "Welcome to FL Studio" or plugin windows


def is_main_title(title: str, pattern: str = MAIN_TITLE, exclude: str = r"coproducer") -> bool:
    """True when a window title is FL Studio's main window (a dialog that merely mentions FL Studio is not)."""
    return bool(re.search(pattern, title, re.I)) and not re.search(exclude, title, re.I)


class WinDesktop:
    def __init__(self, title_pattern: str = MAIN_TITLE, exclude: str = r"coproducer") -> None:
        if sys.platform != "win32":
            raise OSError("WinDesktop only runs on Windows")
        make_dpi_aware()
        self.pattern, self.exclude = re.compile(title_pattern, re.I), re.compile(exclude, re.I)

    # ------------------------------------------------------------------ windows
    def _title(self, h: int) -> str:
        n = _user32().GetWindowTextLengthW(h)
        buf = ctypes.create_unicode_buffer(n + 1)
        _user32().GetWindowTextW(h, buf, n + 1)
        return buf.value

    def _rect(self, h: int) -> tuple[int, int, int, int]:
        r = ctypes.wintypes.RECT()
        _user32().GetWindowRect(h, ctypes.byref(r))
        return (r.left, r.top, r.right, r.bottom)

    def _pid(self, h: int) -> int:
        pid = ctypes.wintypes.DWORD()
        _user32().GetWindowThreadProcessId(h, ctypes.byref(pid))
        return int(pid.value)

    def _info(self, h: int) -> dict:
        return {"handle": int(h), "pid": self._pid(h), "title": self._title(h), "rect": self._rect(h)}

    def all_windows(self) -> list[dict]:
        found: list[dict] = []
        proto = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

        def visit(h, _):
            if _user32().IsWindowVisible(h) and self._title(h):
                found.append(self._info(h))
            return True
        _user32().EnumWindows(proto(visit), 0)
        return found

    def find_window(self) -> dict | None:
        for w in self.all_windows():
            if is_main_title(w["title"], self.pattern.pattern, self.exclude.pattern):
                return w
        return None

    def foreground(self) -> dict:
        return self._info(_user32().GetForegroundWindow())

    def _try_focus(self, handle: int) -> bool:
        _user32().keybd_event(0x12, 0, 0, 0)
        _user32().keybd_event(0x12, 0, 2, 0)
        _user32().ShowWindow(handle, 9)
        _user32().SetForegroundWindow(handle)
        time.sleep(0.15)
        return self.foreground()["handle"] == handle

    def _clear_input_overlay(self, handle: int) -> bool:
        """Windows keeps an invisible full-screen "Windows Input Experience" window in front now and then, and no focus call gets past it,
        but a click on FL does (measured 2026-10-20, a person's click cleared it every time). Click a blank spot of FL's top bar.
        """
        if "input experience" not in self.foreground()["title"].lower():
            return False
        left, top, right, _ = self._rect(handle)
        self.click(left + int((right - left) * 0.76), top + 22)
        time.sleep(0.3)
        return self.foreground()["handle"] == handle

    def focus(self, handle: int) -> bool:
        """Bring a window to the front. Windows may refuse; a tap of Alt lets SetForegroundWindow through.

        When that is not enough (measured 2026-10-20 when the commands run from a background console), SwitchToThisWindow is tried, then this
        thread joins the input queue of the window that has the focus for the moment of the call (AttachThreadInput, user32).
        The invisible input overlay is cleared by a click on FL's top bar before those.
        """
        if self._try_focus(handle):
            return True
        if self._clear_input_overlay(handle):
            return True
        u = _user32()
        u.SwitchToThisWindow(handle, True)              # measured 2026-10-20: takes the focus from the Claude app when SetForegroundWindow is refused
        time.sleep(0.3)
        if self.foreground()["handle"] == handle:
            return True
        theirs = u.GetWindowThreadProcessId(u.GetForegroundWindow(), None)
        mine = ctypes.windll.kernel32.GetCurrentThreadId()
        joined = bool(theirs and theirs != mine and u.AttachThreadInput(mine, theirs, True))
        try:
            u.BringWindowToTop(handle)
            return self._try_focus(handle)
        finally:
            if joined:
                u.AttachThreadInput(mine, theirs, False)

    def windows_of_pid(self, pid: int) -> list[dict]:
        return [w for w in self.all_windows() if w["pid"] == pid]

    def scale(self, handle: int) -> float:
        try:
            return _user32().GetDpiForWindow(handle) / 96.0
        except AttributeError:
            return 1.0

    # ------------------------------------------------------------------ pixels
    def grab(self, rect: tuple[int, int, int, int]) -> Any:
        import mss
        import numpy as np
        left, top, right, bottom = rect
        with mss.mss() as sct:
            shot = sct.grab({"left": left, "top": top, "width": right - left, "height": bottom - top})
        return np.asarray(shot)[:, :, [2, 1, 0]]          # BGRA to RGB

    def save_png(self, arr: Any, path: str) -> None:
        import mss.tools
        h, w = arr.shape[:2]
        mss.tools.to_png(arr.tobytes(), (w, h), output=path)   # arr is RGB; mss writes the bytes as RGB

    # ------------------------------------------------------------------ input
    def click(self, x: int, y: int, button: str = "left", clicks: int = 1, modifiers: tuple = ()) -> None:
        import pyautogui
        for key in modifiers:                     # held for the click only (Shift+click adds a Newtime warp marker)
            pyautogui.keyDown(key)
        try:
            pyautogui.click(x, y, clicks=clicks, button=button)
        finally:
            for key in reversed(modifiers):
                pyautogui.keyUp(key)

    def drag(self, x1: int, y1: int, x2: int, y2: int, seconds: float = 0.4) -> None:
        import pyautogui
        pyautogui.moveTo(x1, y1)
        pyautogui.dragTo(x2, y2, duration=seconds, button="left")

    def type_text(self, text: str, interval: float = 0.02) -> None:
        import pyautogui
        pyautogui.write(text, interval=interval)

    def hotkey(self, keys: list[str]) -> None:
        import pyautogui
        pyautogui.hotkey(*keys)
