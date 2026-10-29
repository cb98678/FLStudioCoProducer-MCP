def test_solos_group_and_remembers(rig):
    rig.fake.mixer[4]["solo"] = True
    r = rig.call("solo_group", indexes=[1, 2])
    assert r.ok and r.meta["verified"] is True and r.value["previous"]["4"] is True
    assert [t["solo"] for t in rig.fake.mixer] == [False, True, True, False, False, False]


def test_failures(rig):
    rig.fake.ignore_writes = True
    assert rig.call("solo_group", indexes=[1]).error.code == "E_NOT_VERIFIED"
