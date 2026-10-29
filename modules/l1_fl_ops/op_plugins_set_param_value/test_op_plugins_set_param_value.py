"""Tests for op_plugins_set_param_value: golden against the fake FL, and failure handling."""
import pytest

from coproducer.fakefl import FakeFL
from coproducer.l1load import load_l1

OP = "op_plugins_set_param_value"
SAMPLE = (0.7, 0, 0, -1)


@pytest.fixture
def fl():
    f = FakeFL().install()
    yield f
    f.uninstall()


def test_matches_fake(fl):
    r = load_l1(OP)(*SAMPLE)
    assert r['ok'] is True
    assert fl.calls('plugins', 'setParamValue')


def test_failures(fl):
    assert load_l1(OP)(*((None,) + SAMPLE[1:]))['error']['code'] == 'E_ARG'
    def boom(*a, **k):
        raise RuntimeError("fl broke")

    setattr(fl.modules["plugins"], "setParamValue", boom)
    r = load_l1(OP)(*SAMPLE)
    assert r["ok"] is False and r["error"]["code"] == "E_INTERNAL"
