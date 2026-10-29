"""A scriptable fake desktop for tests: one FL window, optional dialogs, a log of every input, and changing screenshots."""
from __future__ import annotations

import struct
import zlib
from typing import Callable

import numpy as np

MAIN = {"handle": 100, "pid": 7, "title": "FL Studio 2026", "rect": (0, 0, 640, 360)}


class FakeDesktop:
    def __init__(self) -> None:
        self.main = dict(MAIN)
        self.dialogs: list[dict] = []
        self.fg_pid = 7
        self.refuse_focus = False
        self.dpi = 1.0
        self.log: list[tuple] = []
        self.reactions: list[Callable[["FakeDesktop", tuple], None]] = []
        self.frame = 0

    # windows
    def find_window(self):
        return dict(self.main)

    def foreground(self):
        if self.fg_pid == 7 and self.dialogs:
            return dict(self.dialogs[-1], pid=7)
        return dict(self.main, pid=self.fg_pid) if self.fg_pid == 7 else {"handle": 999, "pid": self.fg_pid, "title": "Other", "rect": (0, 0, 10, 10)}

    def focus(self, handle):
        self.log.append(("focus", handle))
        if not self.refuse_focus:
            self.fg_pid = 7
        return not self.refuse_focus

    def windows_of_pid(self, pid):
        return [dict(self.main)] + [dict(d, pid=7) for d in self.dialogs] if pid == 7 else []

    def scale(self, handle):
        return self.dpi

    # pixels
    def grab(self, rect):
        l, t, r, b = rect
        if getattr(self, "image", None) is not None:          # a test may draw the screen (a fake Newtime, say)
            return self.image[t:b, l:r].copy()
        arr = np.zeros((b - t, r - l, 3), dtype=np.uint8)
        arr[:, :, 0] = (self.frame * 40) % 256
        return arr

    def save_png(self, arr, path):
        h, w = arr.shape[:2]
        raw = b"".join(b"\x00" + arr[y].tobytes() for y in range(h))
        def chunk(tag, data):
            return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        with open(path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))

    # input
    def _do(self, *event):
        self.log.append(event)
        for react in self.reactions:
            react(self, event)

    def click(self, x, y, button="left", clicks=1, modifiers=()):
        self._do("click", x, y, button, clicks, *([tuple(modifiers)] if modifiers else []))

    def drag(self, x1, y1, x2, y2, seconds=0.4):
        self._do("drag", x1, y1, x2, y2)

    def type_text(self, text, interval=0.02):
        self._do("type", text)

    def hotkey(self, keys):
        self._do("hotkey", tuple(keys))

    def script_dialog(self, trigger: tuple, title: str, on_enter=None) -> None:
        """When `trigger` is pressed open a dialog called `title`; text typed into it is kept; Enter closes it and calls on_enter(text)."""
        self.typed = ""

        def react(fake, event):
            if event == ("hotkey", tuple(trigger)):
                fake.open_dialog(title)
            elif event[0] == "type":
                fake.typed = event[1]
            elif event == ("hotkey", ("enter",)) and fake.dialogs:
                fake.close_dialog()
                if on_enter is not None:
                    on_enter(fake.typed)
        self.reactions.append(react)

    def open_dialog(self, title):
        self.dialogs.append({"handle": 200 + len(self.dialogs), "title": title, "rect": (100, 100, 400, 300)})

    def close_dialog(self):
        if self.dialogs:
            self.dialogs.pop()
