import json

from coproducer.services import set_service


def _stub(tmp_path, desk):
    desk.cfg["anchors"] = {"row1": [10, 20]}
    (tmp_path / "recipes").mkdir(exist_ok=True)
    (tmp_path / "recipes" / "place_audio_clip_gui.json").write_text(json.dumps(
        {"name": "place_audio_clip_gui", "verified": True, "params": ["track"],
         "steps": [{"do": "click_row", "anchor": "row1", "param": "track", "dy": 48}]}))
    set_service("recipes_dir", str(tmp_path / "recipes"))


def test_clicks_the_row_of_the_track(rig, desk, tmp_path):
    _stub(tmp_path, desk)
    r = rig.call("add_audio_clip_to_playlist_gui", track=2)
    assert r.ok and ("click", 10, 68, "left", 1) in desk.fake.log


def test_refuses_bad_track_and_halt(rig, desk, tmp_path):
    _stub(tmp_path, desk)
    assert rig.call("add_audio_clip_to_playlist_gui", track=0).error.code == "E_ARG"
    desk.halt.flag = True
    assert rig.call("add_audio_clip_to_playlist_gui", track=1).error.code == "E_HALTED"
