import numpy as np
import soundfile as sf

from coproducer.services import set_service

RATE = 48000


def test_a_bass_note_and_a_vocal_phrase_are_planned(rig, wav, tmp_path):
    set_service("sandbox_root", str(tmp_path / "sandbox"))
    t = np.arange(int(1.2 * RATE)) / RATE
    bass = 0.4 * (np.sin(2 * np.pi * 55.0 * t) + 0.3 * np.sin(2 * np.pi * 110.0 * t))
    r = rig.call("prepare_sampler_sound", path=wav("bass", bass), out_path=str(tmp_path / "sandbox" / "s" / "bass.wav"), role="bass", start_s=0.1, end_s=1.1)
    assert r.ok and r.meta["verified"], r
    v = r.value
    assert v["pitch_note"] == "A1" and v["play_note"] == 60 and abs(v["seconds"] - 1.0) < 0.01
    o = v["oscillator"]
    assert o["sample_playback_source"] == v["path"] and o["octave"] * 12 + o["semitone"] == 27 and o["sample_loop"] == "forward"
    assert sf.info(v["path"]).subtype == "PCM_24"
    vox = 0.3 * np.sin(2 * np.pi * 220.0 * t) * (1 + 0.2 * np.sin(2 * np.pi * 5 * t))
    r2 = rig.call("prepare_sampler_sound", path=wav("vox", np.stack([vox, vox], 1)), out_path=str(tmp_path / "sandbox" / "s" / "vox.wav"), role="vocal")
    assert r2.ok and "semitone" not in r2.value["oscillator"] and r2.value["oscillator"]["sample_loop"] == "off"


def test_failures(rig, wav, tmp_path):
    set_service("sandbox_root", str(tmp_path / "sandbox"))
    x = wav("x", np.zeros(RATE) + 0.1)
    assert rig.call("prepare_sampler_sound", path=x, out_path=str(tmp_path / "out.wav"), role="drum").error.code == "E_SANDBOX_VIOLATION"
    assert rig.call("prepare_sampler_sound", path=x, out_path=str(tmp_path / "sandbox" / "a.wav"), role="drum", start_s=0.5, end_s=0.2).error.code == "E_ARG"
    assert rig.call("prepare_sampler_sound", path=str(tmp_path / "nope.wav"), out_path=str(tmp_path / "sandbox" / "a.wav"), role="drum").error.code == "E_IO"
