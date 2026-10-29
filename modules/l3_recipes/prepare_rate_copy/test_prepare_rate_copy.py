import numpy as np
import soundfile as sf

from coproducer import synth
from coproducer.services import set_service


def test_round_trip_keeps_length_and_pitch(rig, wav, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    src = wav("tone", synth.sine(440, 2.0, 0.5))
    slow = rig.call("prepare_rate_copy", path=src, out_path=str(tmp_path / "slow.wav"), up=442, down=441)
    assert slow.ok and abs(slow.value["ratio"] - 442 / 441) < 1e-4
    back = rig.call("prepare_rate_copy", path=slow.value["out_path"], out_path=str(tmp_path / "back.wav"), up=441, down=442)
    a, _ = sf.read(src)
    b, rate = sf.read(back.value["out_path"])
    assert abs(len(b) - len(a)) <= 2 and rate == 48000
    n = min(len(a), len(b))
    mid = slice(n // 4, 3 * n // 4)
    assert np.max(np.abs(a[mid] - b[mid])) < 1e-2


def test_refuses_bad_ratio_and_paths(rig, wav, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    src = wav("tone", synth.sine(440, 0.5, 0.5))
    assert rig.call("prepare_rate_copy", path=src, out_path=str(tmp_path / "o.wav"), up=3, down=1).error.code in ("E_ARG", "E_SCHEMA")
    assert rig.call("prepare_rate_copy", path=src, out_path="/elsewhere/o.wav", up=442, down=441).error.code == "E_SANDBOX_VIOLATION"
    assert rig.call("prepare_rate_copy", path=str(tmp_path / "none.wav"), out_path=str(tmp_path / "o.wav"), up=1, down=1).error.code == "E_IO"
