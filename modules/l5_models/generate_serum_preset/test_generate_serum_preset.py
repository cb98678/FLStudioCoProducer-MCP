SPEC = {"name": "CP - Test Pluck", "description": "test", "oscillators": [{"volume": 0.75, "custom_harmonics": [[1.0, 0.5, 0.33]]}]}


def test_a_spec_becomes_a_preset_in_the_sandbox_subfolder(rig, ml, tmp_path):
    user = tmp_path / "Serum 2 Presets" / "Presets" / "User"
    user.mkdir(parents=True)
    r = rig.call("generate_serum_preset", spec=SPEC, subfolder="sandbox/test_song", presets_dir=str(user))
    assert r.ok and r.meta["verified"] and r.value["name"] == "CP - Test Pluck"
    assert (user / "sandbox" / "test_song") in __import__("pathlib").Path(r.value["path"]).parents


def test_errors(rig, ml, tmp_path):
    user = tmp_path / "User"
    user.mkdir()
    assert rig.call("generate_serum_preset", spec=SPEC, subfolder="Factory", presets_dir=str(user)).error.code == "E_ARG"
    assert rig.call("generate_serum_preset", spec=SPEC, subfolder="sandbox/../Factory", presets_dir=str(user)).error.code == "E_ARG"
    assert rig.call("generate_serum_preset", spec=SPEC, subfolder="sandbox/x", presets_dir=str(tmp_path / "none")).error.code == "E_NOT_FOUND"
    bad = dict(SPEC, oscillators=[])
    assert rig.call("generate_serum_preset", spec=bad, subfolder="sandbox/x", presets_dir=str(user)).error.code == "E_ARG"
