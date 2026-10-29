"""Tests for op_playlist_select_all: golden against the fake FL, and failure handling."""
import pytest

from coproducer.fakefl import FakeFL
from coproducer.l1load import load_l1

OP = "op_playlist_select_all"
SAMPLE = ()


@pytest.fixture
def fl():
    f = FakeFL().install()
    yield f
    f.uninstall()


def test_matches_fake(fl):
    r = load_l1(OP)(*SAMPLE)
    assert r['ok'] is True
    assert fl.calls('playlist', 'selectAll')


def test_failures(fl):
    def boom(*a, **k):
        raise RuntimeError("fl broke")

    setattr(fl.modules["playlist"], "selectAll", boom)
    r = load_l1(OP)(*SAMPLE)
    assert r["ok"] is False and r["error"]["code"] == "E_INTERNAL"
