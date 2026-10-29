def test_sets_both(rig):
    r = rig.call("set_tempo_and_swing", bpm=150.0, swing=0.25)
    assert r.ok and r.meta["verified"] is True and r.value == {"bpm": 150.0, "swing": 0.25}
    assert rig.fake.tempo == 150.0 and rig.fake.swing == 0.25


def test_failures(rig):
    assert rig.call("set_tempo_and_swing", bpm=150.0, swing=2).error.code == "E_ARG"
    rig.fake.ignore_writes = True
    assert rig.call("set_tempo_and_swing", bpm=150.0, swing=0.2).error.code == "E_NOT_VERIFIED"
