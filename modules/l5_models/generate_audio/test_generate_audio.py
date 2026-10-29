from coproducer.services import set_service


def test_generates_checked_audio(rig, ml, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    r = rig.call("generate_audio", prompt="heavy dubstep bass", out_dir=str(tmp_path / "gen"), duration_s=10, seed=5)
    assert r.ok and r.meta["verified"] and r.value["seed"] == 5 and r.value["paths"][0].endswith("gen_5.wav")


def test_sandbox_and_input_errors(rig, ml, tmp_path):
    assert rig.call("generate_audio", prompt="x y z", out_dir=str(tmp_path)).error.code == "E_SANDBOX_VIOLATION"
    set_service("sandbox_root", str(tmp_path / "box"))
    assert rig.call("generate_audio", prompt="x y z", out_dir=str(tmp_path / "out")).error.code == "E_SANDBOX_VIOLATION"
    assert rig.call("generate_audio", prompt="ab", out_dir=str(tmp_path / "box")).error.code == "E_ARG"
    assert rig.call("generate_audio", prompt="abc", out_dir=str(tmp_path / "box"), duration_s=5).error.code == "E_ARG"
