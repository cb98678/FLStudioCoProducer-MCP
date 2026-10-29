def test_matches(rig):
    rig.fake.mixer[2]["name"] = "Kick"
    r = rig.call("check_open_project", inserts=[{"track": 2, "name": "Kick"}, {"track": 3, "name": "Insert 3"}])
    assert r.ok and r.meta["verified"] and r.value["checked"] == 2


def test_failures(rig):
    r = rig.call("check_open_project", inserts=[{"track": 2, "name": "Kick"}])
    assert r.error.code == "E_ARG" and "Insert 2" in r.error.message
    assert rig.call("check_open_project", inserts=[{"track": 99, "name": "x"}]).error.code == "E_ARG"
