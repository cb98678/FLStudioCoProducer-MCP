import numpy as np

from coproducer import synth


def test_recovers_the_delay(rig, wav):
    a = synth.noise(3.0, 0.2, channels=1, seed=11)
    b = np.vstack([np.zeros((240, 1)), a])[: len(a)]
    r = rig.call("align_bounces", path_a=wav("a", a), path_b=wav("b", b))
    assert r.ok and r.value["lag_samples"] == 240 and r.value["lag_s"] == 0.005 and r.value["correlation"] > 0.99
    assert rig.call("align_bounces", path_a=wav("c", b), path_b=wav("d", a)).value["lag_samples"] == -240


def test_failures(rig, wav, tmp_path):
    a = wav("a", synth.sine(440, 1.0))
    assert rig.call("align_bounces", path_a=a, path_b=str(tmp_path / "no.wav")).error.code == "E_IO"
    assert rig.call("align_bounces", path_a=a, path_b=wav("r", synth.sine(440, 1.0, rate=44100), 44100)).error.code == "E_ARG"
