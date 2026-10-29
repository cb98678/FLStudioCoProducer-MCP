GOOD = """
tempo_source_bpm = 128
tempo_policy = "genre"
free_to_change = ["drums"]
[key]
tonic = "A"
mode = "minor"
[melody]
midi = "specs/a/melody.mid"
contour_threshold = 0.8
[harmony]
chord_loop = ["Am", "F", "C", "G"]
[[sections]]
name = "drop"
bars = 32
"""


def test_reads_complete_invariants(rig, tmp_path):
    f = tmp_path / "i.toml"
    f.write_text(GOOD)
    r = rig.call("load_invariants_file", path=str(f))
    assert r.ok and r.value["harmony"]["chord_loop"][0] == "Am" and r.value["sections"][0]["bars"] == 32


def test_blank_policy_and_missing(rig, tmp_path):
    f = tmp_path / "i.toml"
    f.write_text(GOOD.replace("0.8", '"FILL"'))
    assert rig.call("load_invariants_file", path=str(f)).error.detail["unfilled"] == ["melody.contour_threshold"]
    f.write_text(GOOD.replace('"genre"', '"fast"'))
    assert rig.call("load_invariants_file", path=str(f)).error.code == "E_ARG"
    f.write_text(GOOD.replace("[harmony]", "[harmonyx]"))
    assert "harmony" in rig.call("load_invariants_file", path=str(f)).error.detail["missing"]
    assert rig.call("load_invariants_file", path=str(tmp_path / "gone.toml")).error.code == "E_NOT_FOUND"
