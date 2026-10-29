from hypothesis import given, strategies as st


def test_known_vectors(fn):
    f = fn("decode_sysex")
    assert f([]).value == []
    assert f([0x01, 0x7F]).value == [0xFF]
    assert f([0x01, 0x00, 0x01]).value == [0x80, 0x01]


def test_rejects_bad_input(fn):
    f = fn("decode_sysex")
    assert f([128]).error.code == "E_ARG"
    assert f([0x01]).error.code == "E_ARG"
    assert f([0] * 8 + [0]).error.code == "E_ARG"


@given(st.lists(st.integers(0, 255), max_size=300))
def test_round_trip(fn, data):
    enc = fn("encode_sysex")(data).value
    assert fn("decode_sysex")(enc).value == data
