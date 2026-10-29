import numpy as np
import soundfile as sf


def _tone(tmp_path, pumped: bool):
    rate, bpm = 48000, 120.0
    t = np.arange(int(8 * 0.5 * rate)) / rate  # eight beats
    x = 0.3 * np.sin(2 * np.pi * 110 * t)
    if pumped:
        phase = (t % 0.5) / 0.5
        x *= np.clip(phase * 4, 0.1, 1.0)  # ducks to -20 dB on the beat and recovers over a quarter of the beat
    p = tmp_path / ("p%d.wav" % pumped)
    sf.write(str(p), x, rate)
    return str(p), bpm


def test_pumped_against_flat(rig, tmp_path):
    p, bpm = _tone(tmp_path, True)
    r = rig.call("measure_pump_depth", path=p, bpm=bpm).value
    assert r["depth_db"] > 10 and r["dip_bin"] == 0 and r["beats"] == 8
    f, _ = _tone(tmp_path, False)
    assert rig.call("measure_pump_depth", path=f, bpm=bpm).value["depth_db"] < 1


def test_failures(rig, tmp_path):
    assert rig.call("measure_pump_depth", path=str(tmp_path / "none.wav"), bpm=120).error.code == "E_IO"
    p, _ = _tone(tmp_path, True)
    assert rig.call("measure_pump_depth", path=p, bpm=120, start_s=3.9).error.code == "E_ARG"
