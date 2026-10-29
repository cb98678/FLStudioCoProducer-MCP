FILLED = """
[meta]
name = "mine"
source = "my references"
[loudness]
integrated_lufs = -9.0
integrated_tolerance_lu = 0.5
true_peak_dbtp_ceiling = -1.0
loudness_range_lu = { min = 3.0, max = 8.0 }
[dynamics]
crest_factor_db = { min = 6.0, max = 12.0 }
[stereo]
correlation_floor = 0.2
[clipping]
max_clipped_samples = 0
"""


def test_reads_filled_targets(rig, tmp_path):
    f = tmp_path / "t.toml"
    f.write_text(FILLED)
    r = rig.call("load_targets_file", path=str(f))
    assert r.ok and r.value["name"] == "mine"
    by = {x["label"]: x for x in r.value["limits"]}
    assert by["loudness.integrated_lufs"] == {"label": "loudness.integrated_lufs", "path": "loudness.lufs", "min": -9.5, "max": -8.5}
    assert by["loudness.true_peak_dbtp_ceiling"]["max"] == -1.0 and by["stereo.correlation_floor"]["min"] == 0.2
    assert by["dynamics.crest_factor_db"] == {"label": "dynamics.crest_factor_db", "path": "crest.crest_db", "min": 6.0, "max": 12.0}


def test_refuses_blanks_and_bad_files(rig, tmp_path):
    f = tmp_path / "t.toml"
    f.write_text(FILLED.replace("-9.0", '"FILL: from my reference"'))
    r = rig.call("load_targets_file", path=str(f))
    assert r.error.code == "E_ARG" and r.error.detail["unfilled"] == ["loudness.integrated_lufs"]
    f.write_text("not = [toml")
    assert rig.call("load_targets_file", path=str(f)).error.code == "E_IO"
    assert rig.call("load_targets_file", path=str(tmp_path / "gone.toml")).error.code == "E_NOT_FOUND"
