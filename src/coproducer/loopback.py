"""Test transport: connects the host bridge client to the generated FL-side script and a FakeFL, in process.

Fault injection: drop N reply frames, corrupt the next reply frame, stay busy for N receive calls, or go silent (silent = True).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from .fakefl import FakeEvent, FakeFL

SCRIPT = Path(__file__).resolve().parents[2] / "fl_side" / "device_coproducer.py"


def load_device_script(fake: FakeFL, path: Path | None = None, tag: str = "main"):
    """Import the generated FL-side file with the fake FL modules installed. Returns the module."""
    fake.install()
    name = f"device_coproducer_{tag}_{id(fake)}"
    spec = importlib.util.spec_from_file_location(name, path or SCRIPT)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


class LoopbackTransport:
    def __init__(self, fake: FakeFL, script) -> None:
        self.fake, self.script = fake, script
        self.drop_replies = 0
        self.silent = False  # the dispatcher is gone: every request goes unanswered until this is cleared
        self.corrupt_next = False
        self.busy = 0
        self.sent: list[bytes] = []

    def send(self, data: bytes) -> None:
        self.sent.append(bytes(data))
        self.script.OnSysEx(FakeEvent(bytes(data)))

    def recv(self, timeout: float = 0.0) -> bytes | None:
        if self.busy > 0:
            self.busy -= 1
            return None
        if self.silent:
            self.fake.outbox.clear()
            return None
        if not self.fake.outbox:
            self.script.OnIdle()
        if not self.fake.outbox:
            return None
        frame = self.fake.outbox.pop(0)
        if self.drop_replies > 0:
            self.drop_replies -= 1
            return None
        if self.corrupt_next:
            self.corrupt_next = False
            frame = frame[:-2] + bytes([(frame[-2] + 1) & 0x7F]) + frame[-1:]
        return frame

    def close(self) -> None:
        self.fake.uninstall()
