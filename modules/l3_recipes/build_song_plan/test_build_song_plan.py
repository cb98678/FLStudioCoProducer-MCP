import json
from pathlib import Path

from coproducer import songplan

DATA = Path(__file__).resolve().parents[3] / "tests" / "data"
ARGS = dict(words_file=str(DATA / "friends_vocal_words.json"), hits_file=str(DATA / "friends_drum_hits.json"), name="draft")


def _bass(tmp_path):
    p = tmp_path / "stem_notes.json"
    r = json.loads((DATA / "friends_bass_roots.json").read_text())
    p.write_text(json.dumps({"bass": {"key": r["key"], "roots_per_bar": r["roots_per_bar"]}}))
    return str(p)


def test_drafts_a_valid_plan(rig, desk, tmp_path):
    (tmp_path / "sandbox").mkdir()
    out = str(tmp_path / "sandbox" / "draft.json")
    r = rig.call("build_song_plan", out_plan=out, title="Friends in Low Places", options={"bass_file": _bass(tmp_path)}, **ARGS)
    assert r.ok and r.meta["verified"] and r.value["problems"] == []
    plan = songplan.load(out)
    assert songplan.validate(plan) == [] and plan["key_pc"] == 9 and "check it by ear" in " ".join(plan["notes"])
    assert abs(plan["origin_s"] - 27.3085) < 0.05 and abs(plan["chops"]["hook"]["start"] - 133.82) < 0.5
    assert r.value["downbeat"]["confidence"] > 0


def test_failures(rig, desk, tmp_path):
    (tmp_path / "sandbox").mkdir()
    out = str(tmp_path / "sandbox" / "draft.json")
    assert rig.call("build_song_plan", out_plan="/elsewhere/p.json", options={"key_pc": 9}, **ARGS).error.code == "E_SANDBOX_VIOLATION"
    assert rig.call("build_song_plan", out_plan=out, **ARGS).error.code == "E_ARG"                       # no key
    assert rig.call("build_song_plan", out_plan=out, options={"colour": 1}, **ARGS).error.code == "E_ARG"
    assert rig.call("build_song_plan", out_plan=out, options={"key_pc": 9}, **{**ARGS, "words_file": str(tmp_path / "none.json")}).error.code == "E_IO"
    assert rig.call("build_song_plan", out_plan="", name="x", words_file="a", hits_file="b").error.code == "E_ARG"


def test_a_hand_given_key_does_not_take_another_tonics_mode():
    import importlib.util
    spec = importlib.util.spec_from_file_location("bsp_mode", Path(__file__).with_name("build_song_plan.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _mode_for = mod._mode_for
    assert _mode_for({"tonic_pc": 5, "mode": "major"}, 5) == "major"
    assert _mode_for({"tonic_pc": 9, "mode": "minor"}, 0) == "major"    # A minor's relative major
    assert _mode_for({"tonic_pc": 0, "mode": "major"}, 9) == "minor"    # C major's relative minor
    assert _mode_for({"tonic_pc": 7, "mode": "minor"}, 5) == ""         # Open Your Heart: the bass voted G minor, the key is F
    assert _mode_for({}, 5) == ""
