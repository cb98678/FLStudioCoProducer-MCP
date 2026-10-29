import numpy as np

from coproducer import synth


def test_offset_found_and_located(rig, wav):
    x = np.asarray(synth.sine(440, 4.0, 0.5, channels=2), dtype=float)
    clean = rig.call("measure_dc_offset", path=wav("clean", x))
    assert clean.ok and clean.value["max_dbfs"] < -60 and clean.value["first_held_s"] is None and clean.value["held_s"] == 0
    y = np.concatenate([x, np.zeros((2 * synth.RATE, 2))])
    y[:, 0] -= 0.016                                                              # an offset on the left all through, held after the sound
    r = rig.call("measure_dc_offset", path=wav("dc", y))
    assert r.ok and r.value["first_held_s"] == 4.0 and abs(r.value["held_s"] - 2.0) < 0.06
    assert -37 < r.value["held_dbfs"] < -35 and r.value["max_dbfs"] == r.value["held_dbfs"]
    pulses = np.zeros((4 * synth.RATE, 2))
    for k in range(8):                                                            # kick-like one-sided pulses twice a second: no held offset
        i = k * synth.RATE // 2
        pulses[i: i + 2000] += np.hanning(2000)[:, None] * 0.5
    p = rig.call("measure_dc_offset", path=wav("pulses", pulses))
    assert p.ok and p.value["held_s"] == 0 and p.value["dc_dbfs"] > -40          # one-sided content is a mean, not a held state


def test_failures(rig, tmp_path):
    assert rig.call("measure_dc_offset", path=str(tmp_path / "missing.wav")).error.code == "E_IO"
    assert rig.call("measure_dc_offset", path="").error.code == "E_ARG"
