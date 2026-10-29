"""Tests for op_arrangement_add_auto_time_marker: golden against the fake FL, and failure handling."""
import pytest

from coproducer.fakefl import FakeFL
from coproducer.l1load import load_l1

OP = "op_arrangement_add_auto_time_marker"
SAMPLE = (0, 'Drop')


@pytest.fixture
def fl():
    f = FakeFL().install()
    yield f
    f.uninstall()


def test_matches_fake(fl):
    r = load_l1(OP)(*SAMPLE)
    assert r['ok'] is True
    assert fl.calls('arrangement', 'addAutoTimeMarker')


def test_failures(fl):
    assert load_l1(OP)(*((None,) + SAMPLE[1:]))['error']['code'] == 'E_ARG'
    def boom(*a, **k):
        raise RuntimeError("fl broke")

    setattr(fl.modules["arrangement"], "addAutoTimeMarker", boom)
    r = load_l1(OP)(*SAMPLE)
    assert r["ok"] is False and r["error"]["code"] == "E_INTERNAL"
