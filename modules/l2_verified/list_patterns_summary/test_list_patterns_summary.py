def test_lists_patterns(rig):
    for i in (2, 4):
        rig.fake.patterns[i]["notes"] = [1]
    r = rig.call("list_patterns_summary")
    assert r.ok and [p["index"] for p in r.value] == [2, 4]
    assert r.value[0] == {"index": 2, "name": "Pattern 2", "length": 64}


def test_empty_project_lists_nothing(rig):
    assert rig.call("list_patterns_summary").value == []


def test_surfaces_read_error(rig):
    rig.fake.patterns[1]["notes"] = [1]
    rig.fake.modules["patterns"].getPatternLength = lambda i: 1 / 0
    assert rig.call("list_patterns_summary").error.code == "E_INTERNAL"
