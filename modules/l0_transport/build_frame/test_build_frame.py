def test_known_frame(fn):
    r = fn("build_frame")(1, 4, 300, 0, 1, [])
    assert r.ok
    # 300 = (2 << 7) | 44
    assert r.value == [0xF0, 0x7D, 0x43, 0x50, 1, 4, 2, 44, 0, 0, 0, 1, (1 + 4 + 2 + 44 + 1) & 0x7F, 0xF7]


def test_rejects_bad_fields(fn):
    f = fn("build_frame")
    assert f(128, 1, 0, 0, 1, []).error.code == "E_ARG"
    assert f(1, 1, 16384, 0, 1, []).error.code == "E_ARG"
    assert f(1, 1, 0, 1, 1, []).error.code == "E_ARG"
    assert f(1, 1, 0, 0, 0, []).error.code == "E_ARG"
    assert f(1, 1, 0, 0, 1, [200]).error.code == "E_ARG"
