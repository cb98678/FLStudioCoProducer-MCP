"""Tests for op_raw_call_function against the fake FL."""
import pytest

from coproducer import fl_prelude
from coproducer.fakefl import FakeFL
from coproducer.l1load import load_l1


@pytest.fixture
def fl():
    f = FakeFL().install()
    fl_prelude._RAW_ALLOW.clear()
    yield f
    fl_prelude._RAW_ALLOW.clear()
    f.uninstall()


def test_calls_allowlisted_function(fl):
    fl_prelude._RAW_ALLOW.add("mixer.getTrackName")
    r = load_l1("op_raw_call_function")("mixer", "getTrackName", [1])
    assert r == {"ok": True, "value": "Insert 1", "error": None}


def test_refuses_unlisted_and_missing(fl):
    op = load_l1("op_raw_call_function")
    assert op("mixer", "getTrackName", [1])["error"]["code"] == "E_UNSUPPORTED_API"
    fl_prelude._RAW_ALLOW.add("patterns.getSwing")
    assert op("patterns", "getSwing", [1])["error"]["code"] == "E_UNSUPPORTED_API"
    fl_prelude._RAW_ALLOW.add("mixer.getTrackName")
    assert op("mixer", "getTrackName", "x")["error"]["code"] == "E_ARG"
