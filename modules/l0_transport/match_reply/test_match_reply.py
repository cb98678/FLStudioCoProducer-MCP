def _p(rid, seq, total, payload, typ=2):
    return {"req_id": rid, "seq": seq, "total": total, "payload": payload, "type": typ}


def test_reassembles_out_of_order(fn):
    f = fn("match_reply")
    parsed = [_p(1, 1, 3, [3, 4]), _p(2, 0, 1, [9]), _p(1, 0, 3, [1, 2]), _p(1, 1, 3, [3, 4])]
    assert f(parsed, 1).value["complete"] is False
    parsed.append(_p(1, 2, 3, [5]))
    r = f(parsed, 1)
    assert r.value["complete"] and r.value["payload"] == [1, 2, 3, 4, 5] and r.value["type"] == 2
    assert f(parsed, 99).value == {"complete": False, "have": 0, "total": 0}


def test_total_mismatch(fn):
    r = fn("match_reply")([_p(1, 0, 2, []), _p(1, 1, 3, [])], 1)
    assert r.error.code == "E_ARG"
