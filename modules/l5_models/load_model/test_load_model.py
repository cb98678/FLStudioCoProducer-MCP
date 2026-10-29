def test_loads_and_reuses(rig, ml):
    a = rig.call("load_model", model="demucs")
    assert a.ok and a.value["already_loaded"] is False and a.value["variant"] == "v1"
    assert rig.call("load_model", model="demucs").value["already_loaded"] is True
    assert rig.call("load_model", model="demucs", variant="v2").value["already_loaded"] is False


def test_errors(rig, ml):
    assert rig.call("load_model", model="nope").error.code == "E_NOT_FOUND"
    ml.sched.budget_mb = None
    rig.call("load_model", model="acestep")
    rig.call("load_model", model="flamingo")           # evicts acestep: 12000 + 14000 does not fit in 16000
    assert sorted(ml.sched.resident) == ["flamingo"]
