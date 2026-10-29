def test_builds_bus(rig):
    r = rig.call("build_bus", track_indexes=[1, 2], bus_index=5, name="Drum Bus", level=0.7)
    assert r.ok and r.meta["verified"] is True and r.value["name"] == "Drum Bus" and len(r.value["routes"]) == 2
    assert rig.fake.mixer[5]["name"] == "Drum Bus" and rig.fake.mixer[1]["routes"][5] == 0.7


def test_failures(rig):
    assert rig.call("build_bus", track_indexes=[1], bus_index=99, name="x").error.code == "E_ARG"
    assert rig.call("build_bus", track_indexes=[99], bus_index=5, name="x").error.code == "E_ARG"
