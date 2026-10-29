from coproducer.synth import drum_loop, to_wav


def test_uses_the_model(rig, ml, tmp_path):
    rig.reg.approver = lambda name, kw: True
    p = to_wav(str(tmp_path / "a.wav"), drum_loop(140, bars=4))
    r = rig.call("critique_audio", path=p, focus="low end")
    assert r.ok and r.value["source"] == "model" and "Fake critique of a.wav" in r.value["text"] and "fallback" not in r.meta


def test_falls_back_to_rules(rig, ml, tmp_path):
    rig.reg.approver = lambda name, kw: True
    p = to_wav(str(tmp_path / "a.wav"), drum_loop(140, bars=4))
    ml.sched.registry.pop("flamingo")                              # the optional model is not installed
    r = rig.call("critique_audio", path=p)
    assert r.ok and r.value["source"] == "dsp" and r.meta["fallback"] == "critique_audio_dsp" and r.meta["model_error"] == "E_NOT_FOUND"
    assert rig.call("critique_audio", path=str(tmp_path / "no.wav")).error.code == "E_IO"
    rig.reg.approver = None
    assert rig.call("critique_audio", path=p).error.code == "E_AUTONOMY"
