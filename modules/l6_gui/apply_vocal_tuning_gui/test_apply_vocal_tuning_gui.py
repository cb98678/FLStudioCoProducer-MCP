import json

from coproducer.services import set_service


def _stub(tmp_path):
    (tmp_path / "recipes").mkdir(exist_ok=True)
    (tmp_path / "recipes" / "newtone_tune_save_gui.json").write_text(json.dumps(
        {"name": "newtone_tune_save_gui", "verified": True, "params": ["path", "out_wav", "out_mid", "center", "variation", "trans"],
         "steps": [{"do": "type", "text": "{center} {variation} {trans} {out_mid}"}]}))
    set_service("recipes_dir", str(tmp_path / "recipes"))
    set_service("sandbox_root", str(tmp_path))


def test_runs_the_newtone_recipe_with_the_style_knobs(rig, desk, tmp_path):
    _stub(tmp_path)
    (tmp_path / "v.wav").write_bytes(b"RIFF")
    r = rig.call("apply_vocal_tuning_gui", path=str(tmp_path / "v.wav"), out_path=str(tmp_path / "v_rob.wav"), style="robotic")
    assert r.ok and r.value["midi_path"].endswith("v_rob.mid") and (r.value["center"], r.value["variation"], r.value["trans"]) == (1.0, 0.0, 0.0)
    assert any(e[0] == "type" and e[1].startswith("1.000 0.000 0.000 ") for e in desk.fake.log)
    r2 = rig.call("apply_vocal_tuning_gui", path=str(tmp_path / "v.wav"), out_path=str(tmp_path / "v_s.wav"), style="smooth", trans=0.5)
    assert r2.ok and r2.value["trans"] == 0.5 and r2.value["center"] == 0.83


def test_refuses_bad_style_and_paths(rig, desk, tmp_path):
    _stub(tmp_path)
    assert rig.call("apply_vocal_tuning_gui", path=str(tmp_path / "v.wav"), out_path=str(tmp_path / "o.wav"), style="hard").error.code == "E_ARG"
    assert rig.call("apply_vocal_tuning_gui", path="/elsewhere/v.wav", out_path=str(tmp_path / "o.wav")).error.code == "E_SANDBOX_VIOLATION"
