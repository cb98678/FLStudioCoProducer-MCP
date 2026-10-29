import numpy as np

from coproducer import flpfile, testflp


def _tone(hz, rate=48000, secs=0.6):
    t = np.arange(int(secs * rate)) / rate
    sweep = hz + 2.5 * hz * np.exp(-t / 0.03)  # a kick: a fast drop onto its body pitch
    return (0.8 * np.sin(2 * np.pi * np.cumsum(sweep) / rate) * np.exp(-t / 0.25)).astype(np.float32)


def _src(tmp_path, wav):
    kick = wav("kick_g", _tone(49.0))  # G (49 Hz): A is 2 semitones up, E 3 down
    tom = wav("tom", _tone(150.0))
    hat = wav("hat", (np.random.default_rng(1).standard_normal(20000) * 0.3).astype(np.float32))
    f = testflp.project({0: "Kick", 1: "Tom", 2: "Hat"}, {0: [0, 192], 1: [96], 2: [48]}, samples={0: kick, 1: tom, 2: hat})
    p = tmp_path / "sandbox" / "in.flp"
    p.parent.mkdir(exist_ok=True)
    f.save(str(p))
    return p


def test_tunes_a_kick_to_the_key(rig, desk, tmp_path, wav):
    out = tmp_path / "sandbox" / "tuned.flp"
    r = rig.call("apply_drum_tuning", project=str(_src(tmp_path, wav)), out_project=str(out), key="A")
    assert r.ok and r.meta["verified"] is True and r.value["tuned"] == [0, 1]
    kick, tom = r.value["plan"]
    assert kick["target_note"].startswith("A") and 190 <= kick["cents"] <= 210  # G up to A
    assert tom["target_note"].startswith(("A", "E")) and abs(tom["cents"]) <= 350
    g = flpfile.Flp.load(str(out))
    assert g.channel_pitch(0) == (kick["cents"], 2) and g.channel_pitch(1)[0] == tom["cents"] and g.channel_pitch(2) == (0, 2)


def test_reports_unpitched_and_dry_run(rig, desk, tmp_path, wav):
    out = tmp_path / "sandbox" / "dry.flp"
    r = rig.call("apply_drum_tuning", project=str(_src(tmp_path, wav)), out_project=str(out), key="A", channels=["Hat"], dry_run=True)
    assert r.ok and r.value["plan"][0]["reason"] == "no clear pitch" and not out.exists()


def test_failures(rig, desk, tmp_path, wav):
    src = str(_src(tmp_path, wav))
    out = str(tmp_path / "sandbox" / "x.flp")
    assert rig.call("apply_drum_tuning", project=src, out_project=out, key="H").error.code == "E_ARG"
    assert rig.call("apply_drum_tuning", project=src, out_project=out, key="A", channels=["Nope"]).error.code == "E_ARG"
    assert rig.call("apply_drum_tuning", project=src, out_project="/elsewhere/x.flp", key="A").error.code == "E_SANDBOX_VIOLATION"
