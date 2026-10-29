"""Tests for op_general_undo_up: golden against the fake FL, and failure handling."""
import pytest

from coproducer.fakefl import FakeFL
from coproducer.l1load import load_l1

OP = "op_general_undo_up"
SAMPLE = ()


@pytest.fixture
def fl():
    f = FakeFL().install()
    yield f
    f.uninstall()


def test_matches_fake(fl):
    r = load_l1(OP)(*SAMPLE)
    assert r['ok'] is True
    assert fl.calls('general', 'undoUp')


def test_failures(fl):
    def boom(*a, **k):
        raise RuntimeError("fl broke")

    setattr(fl.modules["general"], "undoUp", boom)
    r = load_l1(OP)(*SAMPLE)
    assert r["ok"] is False and r["error"]["code"] == "E_INTERNAL"
