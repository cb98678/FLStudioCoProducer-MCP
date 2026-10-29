import shutil
from pathlib import Path

from coproducer import serumstate
from coproducer.services import set_service

DATA = Path(__file__).resolve().parents[3] / "tests" / "data"


def _template(tmp_path):
    """A small project whose channel 1 holds a Serum 2 state (the serum-mcp "CP - Deep Sub" channel FL saved)."""
    from coproducer import testflp
    f = testflp.project({0: "Kick", 1: "Sub"}, {0: [0]}, presets={1: "x"})
    f.set_plugin_state(1, (DATA / "serum2_channel_deep_sub.bin").read_bytes())
    out = tmp_path / "serum" / "serum_sounds.flp"
    out.parent.mkdir(parents=True)
    out.write_bytes(f.to_bytes())
    return out


def test_a_preset_is_rendered_and_its_state_kept(rig, ml, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    _template(tmp_path)
    preset = tmp_path / "CP - House Stab.SerumPreset"
    shutil.copyfile(DATA / "cp_house_stab.SerumPreset", preset)
    notes = [{"pitch": 57, "start": 0, "duration": 1}, {"pitch": 60, "start": 1, "duration": 1, "velocity": 90}]
    r = rig.call("render_serum_sound", notes=notes, out_path=str(tmp_path / "audition" / "stab.wav"), preset_path=str(preset), bpm=120)
    assert r.ok and r.meta["verified"] and r.value["preset"] == "CP - House Stab"
    state = Path(r.value["state"]).read_bytes()
    assert serumstate.preset_name(state) == "CP - House Stab" and Path(r.value["wav"]).is_file()
    again = rig.call("render_serum_sound", notes=notes, out_path=str(tmp_path / "audition" / "stab2.wav"), state_path=r.value["state"])
    assert again.ok and again.value["preset"] == "CP - House Stab"


def test_errors(rig, ml, tmp_path):
    set_service("sandbox_root", str(tmp_path / "sb"))
    (tmp_path / "sb").mkdir()
    n = [{"pitch": 60, "start": 0, "duration": 1}]
    assert rig.call("render_serum_sound", notes=n, out_path=str(tmp_path / "sb" / "a.wav")).error.code == "E_ARG"
    assert rig.call("render_serum_sound", notes=n, out_path=str(tmp_path / "outside.wav"), state_path="x").error.code == "E_SANDBOX_VIOLATION"
    assert rig.call("render_serum_sound", notes=n, out_path=str(tmp_path / "sb" / "a.wav"), state_path=str(tmp_path / "none")).error.code == "E_NOT_FOUND"
    bad = tmp_path / "bad.serumstate"
    bad.write_bytes(b"\x0c\x00\x00\x00")
    r = rig.call("render_serum_sound", notes=n, out_path=str(tmp_path / "sb" / "a.wav"), preset_path=str(bad))
    assert r.error.code in ("E_NOT_FOUND", "E_ARG")
