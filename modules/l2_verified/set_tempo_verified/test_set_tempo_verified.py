def test_sets_tempo(rig):
    r = rig.call("set_tempo_verified", bpm=174.0)
    assert r.ok and r.meta["verified"] is True and rig.fake.tempo == 174.0 and r.value == 174.0


def test_failures(rig):
    assert rig.call("set_tempo_verified", bpm=5).error.code == "E_ARG"
    assert rig.call("set_tempo_verified", bpm=1000).error.code == "E_ARG"
    rig.fake.ignore_writes = True
    assert rig.call("set_tempo_verified", bpm=174.0).error.code == "E_NOT_VERIFIED"
