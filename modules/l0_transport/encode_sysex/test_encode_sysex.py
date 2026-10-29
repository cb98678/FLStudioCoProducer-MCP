from hypothesis import given, strategies as st


def test_known_vectors(fn):
    f = fn("encode_sysex")
    assert f([]).value == []
    assert f([0xFF]).value == [0x01, 0x7F]
    assert f([0x80, 0x01]).value == [0x01, 0x00, 0x01]
    assert f([0xFF] * 7).value == [0x7F] * 8
    r = f([0] * 8)
    assert r.ok and r.value == [0] * 10


def test_rejects_bad_input(fn):
    f = fn("encode_sysex")
    for bad in ([256], [-1], ["a"], [True], "abc", None):
        r = f(bad)
        assert not r.ok and r.error.code == "E_ARG"


@given(st.lists(st.integers(0, 255), max_size=300))
def test_output_is_seven_bit(fn, data):
    r = fn("encode_sysex")(data)
    assert r.ok and all(0 <= b <= 127 for b in r.value)
