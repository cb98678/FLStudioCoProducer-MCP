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


def test_one_synth_note_is_lifted_out_of_a_mix_with_its_bend(rig, wav, tmp_path):
    """A saw note on B4 that scoops up from 60 cents flat over 40 ms, over a pad (D#4 and F#4 sines, not its harmonics): isolate keeps the
    note and its scoop and takes the pad out."""
    set_service("sandbox_root", str(tmp_path / "sandbox"))
    t = np.arange(int(0.5 * RATE)) / RATE
    f = 493.88 * 2 ** (np.minimum(0.0, -60 + 1500 * t) / 1200)
    ph = 2 * np.pi * np.cumsum(f) / RATE
    note = 0.3 * sum(np.sin(k * ph) / k for k in range(1, 9)) * np.exp(-3 * t)
    pad = 0.08 * (np.sin(2 * np.pi * 311.13 * t) + np.sin(2 * np.pi * 369.99 * t))
    r = rig.call("prepare_sampler_sound", path=wav("mix", note + pad), out_path=str(tmp_path / "sandbox" / "n" / "note.wav"), role="melodic",
                 options={"isolate": True, "fade_out_s": 0.1, "pitch_midi": 71})
    assert r.ok, r
    v = r.value
    assert v["pitch_note"] == "B4" and v["bend"]["head_cents"] < -25 and abs(v["bend"]["tail_cents"]) < 15
    assert -25 < v["isolation_db"] < -5
    y, sr = sf.read(v["path"], always_2d=True)
    spec = np.abs(np.fft.rfft(y[:, 0] * np.hanning(len(y))))
    hz = np.fft.rfftfreq(len(y), 1 / sr)
    at = lambda f0: spec[np.argmin(np.abs(hz - f0))]  # noqa: E731
    assert at(311.13) < 0.1 * at(493.88) and at(369.99) < 0.1 * at(493.88)
    assert np.max(np.abs(y[-50:])) < 1e-3                                   # the faded tail
    unhinted = rig.call("prepare_sampler_sound", path=wav("mix2", note + pad), out_path=str(tmp_path / "sandbox" / "n" / "n2.wav"), role="melodic")
    assert unhinted.ok and unhinted.value["pitch_note"] != "B4"           # over a B major pad the note alone reads as the chord's root: why pitch_midi exists
    flat = rig.call("prepare_sampler_sound", path=wav("noise", np.random.default_rng(1).normal(0, 0.1, RATE)), out_path=str(tmp_path / "sandbox" / "n" / "x.wav"),
                    role="texture", options={"isolate": True})
    assert flat.error.code == "E_NOT_FOUND"


def test_a_note_a_few_cents_flat_is_tuned_onto_its_semitone(rig, wav, tmp_path):
    set_service("sandbox_root", str(tmp_path / "sandbox"))
    t = np.arange(int(0.6 * RATE)) / RATE
    f = 51.91 * 2 ** (-25 / 1200)                                            # G#1, 25 cents flat (the Pickle remix's bass)
    x = 0.4 * (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t))
    r = rig.call("prepare_sampler_sound", path=wav("b", x), out_path=str(tmp_path / "sandbox" / "b.wav"), role="bass", options={"tune": True})
    assert r.ok and abs(r.value["tuned_cents"] - 25) < 3 and abs(r.value["pitch_midi"] - 32) < 0.05, r
    r2 = rig.call("prepare_sampler_sound", path=wav("b2", x), out_path=str(tmp_path / "sandbox" / "b2.wav"), role="bass", options={"tune": 25})
    assert r2.ok and r2.value["tuned_cents"] == 25 and abs(r2.value["pitch_midi"] - 32) < 0.05, r2
