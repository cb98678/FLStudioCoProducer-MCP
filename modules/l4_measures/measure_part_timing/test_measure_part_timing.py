import numpy as np

from coproducer.testflp import project

RATE = 44100


def _clicks(times, delay=0.0, length=3.0):
    x = np.zeros(int(length * RATE))
    for t in times:
        i = int((t + delay) * RATE)
        x[i : i + 400] = np.hanning(400) * 0.6
    return x


def test_on_grid_and_late(rig, wav, tmp_path):
    f = project({0: "Stab"}, {0: [0, 144, 288, 384, 528]}, bpm=120, bars=2)
    path = str(tmp_path / "p.flp")
    f.save(path)
    times = [t / 96 * 0.5 for t in (0, 144, 288, 384, 528)]
    good = rig.call("measure_part_timing", path=wav("good", _clicks(times, 0.002), RATE), project=path, channel="Stab").value
    assert good["on_grid"] and good["heard"] == 5 and abs(good["median_ms"]) < 10
    late = rig.call("measure_part_timing", path=wav("late", _clicks(times, 0.040), RATE), project=path, channel="Stab").value
    assert 35 < late["median_ms"] < 45
    given = rig.call("measure_part_timing", path=wav("g", _clicks([0.5, 1.0]), RATE), times_s=[0.5, 1.0]).value
    assert given["on_grid"]
    silent = rig.call("measure_part_timing", path=wav("s", np.zeros(RATE), RATE), times_s=[0.2]).value
    assert silent["heard"] == 0


def test_failures(rig, wav, tmp_path):
    clip = wav("c", _clicks([0.5]), RATE)
    assert rig.call("measure_part_timing", path=str(tmp_path / "missing.wav"), times_s=[1.0]).error.code == "E_IO"
    assert rig.call("measure_part_timing", path=clip, times_s=[]).error.code == "E_ARG"
    f = project({0: "Stab"}, {0: [0]})
    p = str(tmp_path / "p.flp")
    f.save(p)
    assert rig.call("measure_part_timing", path=clip, project=p, channel="Nope").error.code == "E_NOT_FOUND"
