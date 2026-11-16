import json
import shutil
from pathlib import Path

import numpy as np

from coproducer import soundpick, testflp
from coproducer.services import set_service
from coproducer.synth import to_wav

DATA = Path(__file__).resolve().parents[3] / "tests" / "data"
RATE = 48000


def _setup(tmp_path):
    """A Serum project to carry presets, a small library (Factory folders, the person's bank, a sandbox folder) and a plucked stem."""
    set_service("sandbox_root", str(tmp_path))
    f = testflp.project({0: "Kick", 1: "Sub"}, {0: [0]}, presets={1: "x"})
    f.set_plugin_state(1, (DATA / "serum2_channel_deep_sub.bin").read_bytes())
    (tmp_path / "serum").mkdir()
    (tmp_path / "serum" / "serum_sounds.flp").write_bytes(f.to_bytes())
    lib = tmp_path / "Serum 2 Presets" / "Presets"
    for rel in ("Factory/Pluck/PL Glass", "Factory/Pluck/PL Wood", "Factory/Chord/CH Warm", "Factory/Bass/Reese/BA Dark",
                "User/CP/CP - Deep Sub", "User/Mine/My Pluck", "User/sandbox/old_song/CP - Old Song Stab"):
        (lib / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(DATA / "cp_house_stab.SerumPreset", str(lib / rel) + ".SerumPreset")
    t = np.arange(int(0.6 * RATE)) / RATE
    note = 0.5 * sum(np.sin(2 * np.pi * k * 220 * t) / k for k in range(1, 20)) * np.exp(-t / 0.15)
    stem = to_wav(str(tmp_path / "other.wav"), np.concatenate([np.concatenate([note, np.zeros(int(0.2 * RATE))]) for _ in range(5)]))
    return stem, lib


def test_the_catalog_takes_the_roles_folders_and_the_persons_banks_but_never_the_sandbox(tmp_path):
    _stem, lib = _setup(tmp_path)
    names = {r["name"] for r in soundpick.catalog(str(lib), "stab")}
    assert names == {"PL Glass", "PL Wood", "CH Warm", "My Pluck"}
    assert {r["name"] for r in soundpick.catalog(str(lib), "bass")} == {"BA Dark"}
    assert soundpick.catalog(str(lib), "sub") == []                   # "CP - Deep Sub" was made for an earlier song: not a candidate
    assert "cp - deep sub" in soundpick.taken({}, "a", "sub")        # the old fixed sounds count as used by the earlier remixes
    one = soundpick.candidates(soundpick.catalog(str(lib), "stab"), "song_a", "stab", set(), 2)
    assert one == soundpick.candidates(soundpick.catalog(str(lib), "stab"), "song_a", "stab", set(), 2)   # the same song hears the same set
    assert len({r["folder"] for r in one}) == 2                       # spread over the folders


def test_each_song_gets_its_own_sound_and_none_comes_back(rig, ml, tmp_path):
    stem, lib = _setup(tmp_path)
    user = lib / "User"
    a = rig.call("select_part_sound", stem=stem, role="stab", name="CP - Song A Stab", song="song_a", out_dir=str(tmp_path / "a"),
                 subfolder="sandbox/song_a", library_dir=str(lib), options={"candidates": 2, "presets_dir": str(user), "rounds": 1})
    assert a.ok and a.meta["verified"] and len(a.value["candidates"]) == 3 and a.value["candidates"][-1]["source"] == "made"
    hist = json.loads((tmp_path / "sound_history.json").read_text())["songs"]
    assert hist["song_a"]["stab"]["preset"] == a.value["preset"]
    b = rig.call("select_part_sound", stem=stem, role="stab", name="CP - Song B Stab", song="song_b", out_dir=str(tmp_path / "b"),
                 subfolder="sandbox/song_b", library_dir=str(lib), options={"candidates": 6, "make": False})
    tried = [c["preset"] for c in b.value["candidates"]]
    assert b.ok and b.value["source"] == "library" and a.value["preset"] not in tried and b.value["preset"] != a.value["preset"]
    assert "CP - Old Song Stab" not in tried and b.value["taken_elsewhere"] >= 4
    again = rig.call("select_part_sound", stem=stem, role="stab", name="CP - Song B Stab", song="song_b", out_dir=str(tmp_path / "b"),
                     subfolder="sandbox/song_b", library_dir=str(lib), options={"candidates": 6, "make": False})
    assert again.value["preset"] == b.value["preset"]                  # a re-run of the same song keeps its own choice open


def test_errors(rig, ml, tmp_path):
    stem, lib = _setup(tmp_path)
    kw = {"stem": stem, "role": "stab", "name": "x", "song": "s", "subfolder": "sandbox/s", "library_dir": str(lib)}
    assert rig.call("select_part_sound", out_dir=str(tmp_path.parent / "out"), **kw).error.code == "E_SANDBOX_VIOLATION"
    r = rig.call("select_part_sound", out_dir=str(tmp_path / "o"), **{**kw, "library_dir": str(tmp_path / "none")}, options={"make": False})
    assert r.error.code == "E_NOT_FOUND"
    quiet = to_wav(str(tmp_path / "quiet.wav"), np.zeros(RATE))
    assert rig.call("select_part_sound", out_dir=str(tmp_path / "o"), **{**kw, "stem": quiet}).error.code == "E_NOT_FOUND"
