import numpy as np
import soundfile as sf

from coproducer.services import set_service
from coproducer.synth import drum_loop


def _mix(path):
    x = np.asarray(drum_loop(128, bars=8), dtype=float)
    sf.write(path, (x / np.abs(x).max() * 0.4).astype("float32"), 44100)
    return path


def test_masters_to_the_club_target(rig, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    r = rig.call("apply_club_master", path=_mix(str(tmp_path / "mix.wav")), targets_file="targets/club_release.toml", out_path=str(tmp_path / "m.wav"))
    assert r.ok and r.meta["verified"], r
    m = r.value["measured"]
    assert abs(m["lufs"] + 8.0) <= 1.0 and m["true_peak_dbtp"] <= -0.35 and m["crest_db"] >= 6.4
    assert sf.info(str(tmp_path / "m.wav")).subtype == "PCM_24"
    assert rig.call("measure_dc_offset", path=str(tmp_path / "m.wav")).value["max_dbfs"] < -60     # the clipper's DC is taken out too


def test_errors_and_crest_floor(rig, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    mix = _mix(str(tmp_path / "mix.wav"))
    assert rig.call("apply_club_master", path=mix, targets_file="targets/club_release.toml", out_path="/elsewhere/m.wav").error.code == "E_SANDBOX_VIOLATION"
    assert rig.call("apply_club_master", path=str(tmp_path / "no.wav"), targets_file="targets/club_release.toml", out_path=str(tmp_path / "m.wav")).error.code == "E_NOT_FOUND"
    r = rig.call("apply_club_master", path=mix, targets_file="targets/club_release.toml", out_path=str(tmp_path / "loud.wav"), lufs=-4.0)
    assert r.ok and r.value["stopped"] == "crest_floor" and not r.meta["verified"]      # too loud for the crest floor: reported, not forced


def test_matches_the_reference_tonal_balance(rig, tmp_path):
    """A dull mix against bright references: the EQ lifts the top, and the master sits closer to the references' range than the mix did."""
    set_service("sandbox_root", str(tmp_path))
    from scipy.signal import butter, sosfilt
    x = np.asarray(drum_loop(128, bars=8), dtype=float)
    dull = sosfilt(butter(2, 2500, fs=44100, output="sos"), x, axis=0)
    sf.write(str(tmp_path / "mix.wav"), (dull / np.abs(dull).max() * 0.4).astype("float32"), 44100)
    for i, g in enumerate((0.8, 0.6)):
        sf.write(str(tmp_path / ("ref%d.wav" % i)), (x / np.abs(x).max() * g).astype("float32"), 44100)
    p = rig.call("build_reference_profile", paths=[str(tmp_path / "ref0.wav"), str(tmp_path / "ref1.wav")], out_file=str(tmp_path / "prof.json"))
    assert p.ok
    r = rig.call("apply_club_master", path=str(tmp_path / "mix.wav"), targets_file="targets/club_release.toml", out_path=str(tmp_path / "m.wav"),
                 profile=str(tmp_path / "prof.json"))
    assert r.ok, r
    t = r.value["tonal"]
    assert max(t["gains_db"]) > 1.0 and t["after"]["rms_db"] < t["before"]["rms_db"]
    assert r.value["measured"]["true_peak_dbtp"] <= -0.35
    assert rig.call("apply_club_master", path=str(tmp_path / "mix.wav"), targets_file="targets/club_release.toml", out_path=str(tmp_path / "m2.wav"),
                    profile=str(tmp_path / "none.json")).error.code == "E_NOT_FOUND"
