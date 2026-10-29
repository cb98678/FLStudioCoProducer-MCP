def test_restores_states(rig):
    rig.fake.mixer[4]["solo"] = True
    prev = rig.call("solo_group", indexes=[1]).value["previous"]
    r = rig.call("restore_solo_group", previous=prev)
    assert r.ok and r.meta["verified"] is True and [t["solo"] for t in rig.fake.mixer] == [False, False, False, False, True, False]


def test_failures(rig):
    assert rig.call("restore_solo_group", previous={"99": True}).error.code == "E_ARG"
