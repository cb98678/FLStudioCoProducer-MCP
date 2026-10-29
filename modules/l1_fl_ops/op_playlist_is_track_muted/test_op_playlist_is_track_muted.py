"""Tests for op_playlist_is_track_muted: golden against the fake FL, and failure handling."""
import pytest

from coproducer.fakefl import FakeFL
from coproducer.l1load import load_l1

OP = "op_playlist_is_track_muted"
SAMPLE = (1,)


@pytest.fixture
def fl():
    f = FakeFL().install()
    yield f
    f.uninstall()


def test_matches_fake(fl):
    r = load_l1(OP)(*SAMPLE)
    want = fl.modules['playlist'].isTrackMuted(*SAMPLE)
    assert r['ok'] is True
    assert r['value'] == want


def test_failures(fl):
    assert load_l1(OP)(*((None,) + SAMPLE[1:]))['error']['code'] == 'E_ARG'
    def boom(*a, **k):
        raise RuntimeError("fl broke")

    setattr(fl.modules["playlist"], "isTrackMuted", boom)
    r = load_l1(OP)(*SAMPLE)
    assert r["ok"] is False and r["error"]["code"] == "E_INTERNAL"
