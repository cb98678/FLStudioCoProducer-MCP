def test_creates_route_and_level(rig):
    r = rig.call("create_send_route", source_index=2, bus_index=4, level=0.5)
    assert r.ok and r.meta["verified"] is True and r.value == {"source": 2, "bus": 4, "level": 0.5}
    assert rig.fake.mixer[2]["routes"][4] == 0.5


def test_failures(rig):
    assert rig.call("create_send_route", source_index=2, bus_index=99).error.code == "E_ARG"
    rig.fake.ignore_writes = True
    assert rig.call("create_send_route", source_index=2, bus_index=4).error.code == "E_NOT_VERIFIED"
