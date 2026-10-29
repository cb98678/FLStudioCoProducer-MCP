import json
import tomllib

import numpy as np
import soundfile as sf

from coproducer.services import set_service
from coproducer.synth import drum_loop


def _ref(path, gain, bright=False):
    x = np.asarray(drum_loop(128, bars=4), dtype=float)
    if bright:
        x = np.diff(x, axis=0, prepend=x[:1])
    sf.write(path, (x / np.abs(x).max() * gain).astype("float32"), 44100)
    return str(path)


def test_profile_and_targets_from_references(rig, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    refs = [_ref(tmp_path / "a.wav", 0.9), _ref(tmp_path / "b.flac", 0.7)]
    r = rig.call("build_reference_profile", paths=refs, out_file=str(tmp_path / "refs" / "house.json"), targets_out=str(tmp_path / "refs" / "house.toml"))
    assert r.ok and r.meta["verified"] and r.value["tracks"] == 2, r
    prof = json.loads((tmp_path / "refs" / "house.json").read_text())
    assert len(prof["tonal"]["mean_db"]) == 29 and prof["tonal"]["tracks"] == 2
    t = tomllib.loads((tmp_path / "refs" / "house.toml").read_text())
    assert t["loudness"]["integrated_lufs"] == r.value["summary"]["lufs"]["median"]
    assert t["loudness"]["true_peak_dbtp_ceiling"] == -0.5                       # the delivery ceiling is kept from the base file
    assert t["spectrum"]["reference_profile"].endswith("house.json")
    assert rig.call("load_targets_file", path=str(tmp_path / "refs" / "house.toml")).ok


def test_refuses_outside_sandbox_and_unreadable_files(rig, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    ref = _ref(tmp_path / "a.wav", 0.9)
    assert rig.call("build_reference_profile", paths=[ref], out_file="/elsewhere/p.json").error.code == "E_SANDBOX_VIOLATION"
    assert rig.call("build_reference_profile", paths=[str(tmp_path / "nope.wav")], out_file=str(tmp_path / "p.json")).error.code == "E_NOT_FOUND"
    (tmp_path / "junk.m4a").write_bytes(b"not audio")
    assert rig.call("build_reference_profile", paths=[str(tmp_path / "junk.m4a")], out_file=str(tmp_path / "p.json")).error.code == "E_IO"
