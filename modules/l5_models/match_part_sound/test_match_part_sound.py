from pathlib import Path

import numpy as np

from coproducer import serumstate, testflp
from coproducer.services import set_service
from coproducer.synth import to_wav

DATA = Path(__file__).resolve().parents[3] / "tests" / "data"
RATE = 48000


def _setup(tmp_path):
    set_service("sandbox_root", str(tmp_path))
    f = testflp.project({0: "Kick", 1: "Sub"}, {0: [0]}, presets={1: "x"})
    f.set_plugin_state(1, (DATA / "serum2_channel_deep_sub.bin").read_bytes())
    (tmp_path / "serum").mkdir()
    (tmp_path / "serum" / "serum_sounds.flp").write_bytes(f.to_bytes())
    user = tmp_path / "Serum 2 Presets" / "Presets" / "User"
    user.mkdir(parents=True)
    t = np.arange(int(0.6 * RATE)) / RATE
    note = 0.5 * sum(np.sin(2 * np.pi * k * 220 * t) / k for k in range(1, 20)) * np.exp(-t / 0.15)
    stem = to_wav(str(tmp_path / "other.wav"), np.concatenate([np.concatenate([note, np.zeros(int(0.2 * RATE))]) for _ in range(5)]))
    return stem, user


def test_a_part_is_matched_in_rounds_and_the_best_kept(rig, ml, tmp_path):
    stem, user = _setup(tmp_path)
    r = rig.call("match_part_sound", stem=stem, role="pluck", name="CP - Test Song Pluck", out_dir=str(tmp_path / "sounds"),
                 subfolder="sandbox/test_song", options={"presets_dir": str(user), "rounds": 2})
    assert r.ok and r.meta["verified"] and len(r.value["rounds"]) == 2           # the fake's tone never matches a pluck: both rounds run
    assert serumstate.preset_name(Path(r.value["state"]).read_bytes()) == "CP - Test Song Pluck"
    assert r.value["rounds"][0]["changes"] and (tmp_path / "sounds" / "CP___Test_Song_Pluck_match.json").is_file()
    assert "plucked (short decay)" in r.value["words"]


def test_errors(rig, ml, tmp_path):
    stem, user = _setup(tmp_path)
    assert rig.call("match_part_sound", stem=stem, role="pluck", name="x", out_dir=str(tmp_path.parent / "out"), subfolder="sandbox/a").error.code == "E_SANDBOX_VIOLATION"
    quiet = to_wav(str(tmp_path / "quiet.wav"), np.zeros(RATE))
    assert rig.call("match_part_sound", stem=quiet, role="pluck", name="x", out_dir=str(tmp_path / "s"), subfolder="sandbox/a").error.code == "E_NOT_FOUND"
    r = rig.call("match_part_sound", stem=stem, role="pluck", name="x", out_dir=str(tmp_path / "s"), subfolder="sandbox/a",
                 options={"presets_dir": str(tmp_path / "nowhere")})
    assert r.error.code == "E_NOT_FOUND" and r.error.detail["rounds"][0]["round"] == 1
