def test_unloads(rig, ml):
    rig.call("load_model", model="demucs")
    r = rig.call("unload_model", model="demucs")
    assert r.value == {"model": "demucs", "was_loaded": True} and ml.sched.resident == {}


def test_not_loaded_is_fine(rig, ml):
    assert rig.call("unload_model", model="demucs").value["was_loaded"] is False
