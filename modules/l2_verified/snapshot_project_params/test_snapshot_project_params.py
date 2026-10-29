def test_reads_slots_params_and_channels(rig):
    r = rig.call("snapshot_project_params", inserts=[0, 1], max_params=50)
    assert r.ok, r.error
    ins = {i["index"]: i for i in r.value["inserts"]}
    assert set(ins) == {0, 1} and "routes" in ins[1] and ins[0]["volume"] is not None
    slots = [s for i in ins.values() for s in i["slots"]]
    assert slots and all(s["params"] for s in slots) and all("text" in p for s in slots for p in s["params"].values())
    assert r.value["channels"] and "name" in r.value["channels"][0]
    lean = rig.call("snapshot_project_params", inserts=[1], include_channels=False).value
    assert lean["channels"] == []


def test_failures(rig):
    assert rig.call("snapshot_project_params", inserts=[]).error.code == "E_ARG"
    assert rig.call("snapshot_project_params", inserts=[999]).error.code == "E_ARG"
