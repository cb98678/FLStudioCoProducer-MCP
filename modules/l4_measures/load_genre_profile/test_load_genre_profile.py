

GOOD = """
[meta]
name = "x"
[tempo]
range_bpm = [140, 150]
feel = "half_time"
[structure]
sections = [{ name = "drop", bars = 32 }]
[drums]
kick_pattern_steps = [0, 10]
[bass]
patch_family = ["my synth"]
register_hz = [40, 200]
[mix]
targets = "targets/streaming_default.toml"
bus_layout = ["drums", "bass"]
"""


def test_reads_complete_profile(rig, tmp_path):
    f = tmp_path / "p.toml"
    f.write_text(GOOD)
    r = rig.call("load_genre_profile", path=str(f))
    assert r.ok and r.value["profile"]["tempo"]["feel"] == "half_time" and r.value["unfilled"] == []


def test_blanks_and_missing_tables(rig, tmp_path):
    f = tmp_path / "p.toml"
    f.write_text(GOOD.replace("[140, 150]", '["FILL", "FILL"]'))
    assert rig.call("load_genre_profile", path=str(f)).error.detail["unfilled"] == ["tempo.range_bpm.0", "tempo.range_bpm.1"]
    assert rig.call("load_genre_profile", path=str(f), allow_blanks=True).ok
    f.write_text(GOOD.replace("[bass]", "[bass_x]"))
    assert "bass" in rig.call("load_genre_profile", path=str(f)).error.detail["missing"]
    assert rig.call("load_genre_profile", path=str(tmp_path / "gone.toml")).error.code == "E_NOT_FOUND"
