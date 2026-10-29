from hypothesis import given, strategies as st


def test_round_trip_with_build(fn):
    frame = fn("build_frame")(1, 1, 5000, 2, 9, [1, 2, 3]).value
    r = fn("parse_frame")(frame)
    assert r.ok
    assert r.value == {"version": 1, "type": 1, "req_id": 5000, "seq": 2, "total": 9, "payload": [1, 2, 3]}


def test_rejects_damaged_frames(fn):
    build, parse = fn("build_frame"), fn("parse_frame")
    frame = build(1, 1, 7, 0, 1, [9, 9]).value
    assert parse(frame[:-1]).error.detail["not_ours"]
    assert parse([0xF0, 0x7E] + frame[2:]).error.detail["not_ours"]
    bad = list(frame)
    bad[10] ^= 0x01
    assert parse(bad).error.detail.get("bad_checksum")


@given(st.integers(0, 127), st.integers(0, 16383), st.lists(st.integers(0, 127), max_size=60), st.integers(0, 40))
def test_single_byte_flip_is_detected(fn, typ, rid, payload, pos):
    frame = fn("build_frame")(1, typ, rid, 0, 1, payload).value
    i = 4 + pos % (len(frame) - 6)  # a byte between the prefix and the checksum
    bad = list(frame)
    bad[i] = (bad[i] + 1) & 0x7F
    assert not fn("parse_frame")(bad).ok
