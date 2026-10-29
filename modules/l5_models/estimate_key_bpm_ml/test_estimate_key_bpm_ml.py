def test_parses_the_reply(rig, ml):
    r = rig.call("estimate_key_bpm_ml", path="a.wav")
    assert r.ok and r.value == {"key": "A Minor", "bpm": 128.0, "source": "model"}


def test_unparseable_reply(rig, ml, monkeypatch):
    monkeypatch.setenv("FAKE_CRITIQUE_REPLY", "It feels like a jazzy minor groove")
    r = rig.call("estimate_key_bpm_ml", path="a.wav")
    assert r.error.code == "E_MODEL" and "jazzy" in r.error.detail["reply"]
    ml.sched.registry.pop("flamingo")
    assert rig.call("estimate_key_bpm_ml", path="a.wav").error.code == "E_NOT_FOUND"
