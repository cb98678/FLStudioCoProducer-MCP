def test_encodes(fn):
    r = fn("encode_body")("op_x", {"a": 1, "b": "é"})
    assert r.ok
    assert bytes(r.value).decode() == 'op_x\x1f{"a":1,"b":"\\u00e9"}'


def test_rejects_bad_input(fn):
    f = fn("encode_body")
    assert f("", {}).error.code == "E_ARG"
    assert f("a\x1fb", {}).error.code == "E_ARG"
    assert f("a", {"x": object()}).error.code == "E_ARG"
