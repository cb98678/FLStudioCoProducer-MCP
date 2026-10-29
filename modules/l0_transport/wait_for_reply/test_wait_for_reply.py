from pathlib import Path

from coproducer.registry import Registry
from coproducer.services import set_service

ROOT = Path(__file__).resolve().parents[2]


class _T:
    def __init__(self, frames):
        self.q = list(frames)

    def recv(self, timeout):
        return bytes(self.q.pop(0)) if self.q else None


def _reg():
    r = Registry(ROOT / "l0_transport").load()
    r.activate()
    return r


def test_collects_split_reply(fn):
    reg = _reg()
    build = reg.modules["build_frame"].fn
    frames = [build(1, 2, 77, 1, 2, [4, 5]).value, build(1, 2, 12, 0, 1, [9]).value, build(1, 2, 77, 0, 2, [1, 2, 3]).value]
    set_service("transport", _T(frames))
    r = fn("wait_for_reply")(77, 1.0)
    assert r.ok and r.value == {"type": 2, "payload": [1, 2, 3, 4, 5]}


def test_times_out(fn):
    _reg()
    set_service("transport", _T([]))
    r = fn("wait_for_reply")(5, 0.15)
    assert r.error.code == "E_TIMEOUT" and r.error.retryable
