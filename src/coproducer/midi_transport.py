"""Real bridge transport over two MIDI ports (loopMIDI on Windows). Same send/recv shape as LoopbackTransport."""
from __future__ import annotations

import re
import time
from typing import Any

from .result import Result, fail, ok


class MidiTransport:
    def __init__(self, out_port: Any, in_port: Any, backend: Any) -> None:
        self.out_port, self.in_port, self.backend = out_port, in_port, backend

    def send(self, data: bytes) -> None:
        self.out_port.send(self.backend.Message.from_bytes(list(data)))

    def recv(self, timeout: float = 0.0) -> bytes | None:
        """Return the next SysEx message as bytes (F0 to F7), or None when nothing arrives within timeout seconds."""
        end = time.monotonic() + timeout
        while True:
            msg = self.in_port.poll()
            if msg is None:
                if time.monotonic() >= end:
                    return None
                time.sleep(0.002)
            elif msg.type == "sysex":
                return bytes(msg.bytes())

    def close(self) -> None:
        for p in (self.out_port, self.in_port):
            try:
                p.close()
            except Exception:  # noqa: BLE001 - closing is best effort
                pass


def resolve_port_name(wanted: str, available: list[str]) -> str | None:
    """Match a configured port name to a name the MIDI backend reports.

    Windows reports loopMIDI ports with an index ("coproducer-in 1"), so an exact match is tried first, then the same
    name ignoring case, then the name followed by an index, then any name that starts with it.
    """
    for test in (
        lambda n: n == wanted,
        lambda n: n.lower() == wanted.lower(),
        lambda n: re.fullmatch(re.escape(wanted) + r"[ _-]?\d+", n, re.IGNORECASE) is not None,
        lambda n: n.lower().startswith(wanted.lower()),
    ):
        hit = [n for n in available if test(n)]
        if hit:
            return hit[0]
    return None


def _names(backend: Any, kind: str) -> list[str]:
    getter = getattr(backend, "get_%s_names" % kind, None)
    return list(getter()) if getter else []


def open_midi_transport(out_name: str, in_name: str, backend: Any = None) -> Result:
    """Open the named ports with mido (or another backend with the same names) and wrap them.

    The names may omit the index Windows adds. On failure the error lists the ports the backend can see.
    """
    if backend is None:
        try:
            import mido as backend  # type: ignore[no-redef]
        except ImportError:
            return fail("E_UNSUPPORTED_API", "install mido and python-rtmidi to use MIDI ports")
    outs, ins = _names(backend, "output"), _names(backend, "input")
    # When the backend cannot list ports, fall back to the names as given.
    real_out = resolve_port_name(out_name, outs) if outs else out_name
    real_in = resolve_port_name(in_name, ins) if ins else in_name
    if real_out is None or real_in is None:
        missing = [n for n, r in ((out_name, real_out), (in_name, real_in)) if r is None]
        return fail("E_IO", "cannot find MIDI port %s. Output ports seen: %s. Input ports seen: %s. "
                    "In loopMIDI, create the ports and keep loopMIDI running." % (" and ".join(map(repr, missing)), outs or "none", ins or "none"),
                    outputs=outs, inputs=ins)
    try:
        return ok(MidiTransport(backend.open_output(real_out), backend.open_input(real_in), backend), out=real_out, inp=real_in)
    except Exception as e:  # noqa: BLE001
        return fail("E_IO", "cannot open MIDI ports %r and %r: %s" % (real_out, real_in, e))
