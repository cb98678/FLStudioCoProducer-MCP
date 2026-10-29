from coproducer.synth import drum_loop, to_wav


def test_similarity_against_references_and_a_baseline(rig, ml, tmp_path):
    a = to_wav(str(tmp_path / "remix.wav"), drum_loop(128, bars=2))
    ref = to_wav(str(tmp_path / "ref.wav"), drum_loop(126, bars=2))
    r = rig.call("compare_to_references_ml", path=a, references=[ref], windows=[[0, 2], [2, 4]], baseline=ref)
    assert r.ok and r.meta["verified"] and len(r.value["scores"]) == 2 and "closer_than_baseline" in r.value
    assert all(-1.0 <= s <= 1.0001 for s in r.value["scores"])


def test_errors(rig, ml, tmp_path):
    a = to_wav(str(tmp_path / "remix.wav"), drum_loop(128, bars=1))
    assert rig.call("compare_to_references_ml", path=a, references=[str(tmp_path / "none.wav")]).error.code == "E_NOT_FOUND"
