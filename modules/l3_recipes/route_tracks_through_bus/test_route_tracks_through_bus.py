def test_routes_through_the_bus(rig):
    r = rig.call("route_tracks_through_bus", sources=[1, 2], bus_index=5, name="Drums Bus")
    assert r.ok and r.meta["verified"]
    m = rig.fake.mixer
    assert m[5]["name"] == "Drums Bus" and set(m[1]["routes"]) == {5} and set(m[2]["routes"]) == {5} and m[1]["routes"][5] == 0.8
    assert m[5]["routes"] == {0: 0.8} and m[3]["routes"] == {0: 0.8}  # the bus reaches the master, other tracks are untouched
    assert rig.call("route_tracks_through_bus", sources=[1, 2], bus_index=5, name="Drums Bus").ok  # idempotent


def test_carries_each_sources_own_level(rig):
    rig.fake.mixer[1]["routes"][0] = 0.6
    r = rig.call("route_tracks_through_bus", sources=[1, 2], bus_index=5, name="Drums Bus")
    assert r.ok and rig.fake.mixer[1]["routes"][5] == 0.6 and rig.fake.mixer[2]["routes"][5] == 0.8
    assert rig.call("route_tracks_through_bus", sources=[3], bus_index=5, name="Drums Bus", level=0.5).ok and rig.fake.mixer[3]["routes"][5] == 0.5


def test_failures(rig):
    assert rig.call("route_tracks_through_bus", sources=[1], bus_index=99, name="x").error.code == "E_ARG"
    assert rig.call("route_tracks_through_bus", sources=[99], bus_index=5, name="x").error.code == "E_ARG"
    assert rig.call("route_tracks_through_bus", sources=[], bus_index=5, name="x").error.code == "E_ARG"
