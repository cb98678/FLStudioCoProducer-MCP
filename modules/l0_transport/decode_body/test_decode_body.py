from hypothesis import given, strategies as st


def test_round_trip(fn):
    body = fn("encode_body")("op_y", {"k": [1, 2.5, None, True], "s": "x\ny"}).value
    r = fn("decode_body")(body)
    assert r.value == {"name": "op_y", "data": {"k": [1, 2.5, None, True], "s": "x\ny"}}


def test_rejects_bad_bodies(fn):
    f = fn("decode_body")
    assert f(list(b"nosep")).error.code == "E_ARG"
    assert f(list(b"a\x1f[1]")).error.code == "E_ARG"
    assert f([0xFF, 0xFE]).error.code == "E_ARG"
    assert f(list(b"\x1f{}")).error.code == "E_ARG"


@given(st.dictionaries(st.text(min_size=1, max_size=6), st.one_of(st.integers(-10**9, 10**9), st.text(max_size=12), st.booleans(), st.none()), max_size=6))
def test_property_round_trip(fn, data):
    assert fn("decode_body")(fn("encode_body")("op", data).value).value["data"] == data
