"""Each song's own sounds (the person, 2026-11-07): no part has a default sound; remix_song chooses one per part and the bass, and the
history keeps a sound from coming back in another song."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import numpy as np

import remix_song
from coproducer import remixbuild, testflp
from coproducer.services import set_service
from coproducer.synth import to_wav

DATA = Path(__file__).resolve().parent / "data"
RATE = 48000


def _song(tmp_path):
    set_service("sandbox_root", str(tmp_path))
    f = testflp.project({0: "Kick", 1: "Sub"}, {0: [0]}, presets={1: "x"})
    f.set_plugin_state(1, (DATA / "serum2_channel_deep_sub.bin").read_bytes())
    (tmp_path / "serum").mkdir()
    (tmp_path / "serum" / "serum_sounds.flp").write_bytes(f.to_bytes())
    lib = tmp_path / "lib" / "Presets"
    for rel in ("Factory/Pluck/PL One", "Factory/Chord/CH Two", "Factory/Arp/AR Three", "Factory/Bass/Sub/SB Four", "Factory/Bass/Reese/BA Five",
                "Factory/Bass/Synth/BA Six"):
        (lib / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(DATA / "cp_house_stab.SerumPreset", str(lib / rel) + ".SerumPreset")
    (lib / "User").mkdir()
    t = np.arange(int(0.6 * RATE)) / RATE
    note = 0.5 * sum(np.sin(2 * np.pi * k * 110 * t) / k for k in range(1, 20)) * np.exp(-t / 0.3)
    take = np.concatenate([np.concatenate([note, np.zeros(int(0.2 * RATE))]) for _ in range(5)])
    stems = {"other": to_wav(str(tmp_path / "other.wav"), take), "bass": to_wav(str(tmp_path / "bass.wav"), take)}
    work = tmp_path / "remix" / "w"
    work.mkdir(parents=True)
    plan = work / "plan.json"
    plan.write_text(json.dumps({"key_pc": 9}), encoding="utf-8")
    return lib, stems, work, plan


def _args(name, lib, serum, sounds="choose"):
    return SimpleNamespace(style="tech_house", name=name, preset_library=str(lib), match_to=[], serum_preset=[], sounds=sounds, candidates=2,
                           sound_seed="", serum=str(serum))


def test_every_part_and_the_bass_get_this_songs_own_sound(rig, ml, tmp_path):
    lib, stems, work, plan = _song(tmp_path)
    report: dict = {}

    def step(label, module, **kw):
        return rig.call(module, **kw)
    states = remix_song.choose_sounds(_args("song_a", lib, tmp_path / "serum" / "serum_sounds.flp", "library"), plan, stems, "", work, {}, step, report)
    assert set(states) == {"stab", "arp", "sub"}                           # the tech-house engine's three synth parts
    bass = json.loads(plan.read_text())["bass_sample"]
    assert bass["root_midi"] == 33 and Path(bass["file"]).is_file() and bass["label"].startswith("Bass - ")
    picked = {p: report["sounds"][p]["preset"] for p in ("stab", "arp", "sub", "bass")}
    assert len(set(picked.values())) == 4                                   # no two parts of one song share a sound
    plan.write_text(json.dumps({"key_pc": 9}), encoding="utf-8")
    report2: dict = {}
    remix_song.choose_sounds(_args("song_b", lib, tmp_path / "serum" / "serum_sounds.flp", "library"), plan, stems, "", work, {}, step, report2)
    for part in ("stab", "arp", "sub", "bass"):                             # another song never gets a sound the first one took
        got = report2["sounds"].get(part, {}).get("preset")
        assert got not in picked.values()


def test_the_build_has_no_default_sound_and_names_its_stand_ins():
    assert not hasattr(remixbuild, "SERUM_PRESETS") and remixbuild.SERUM_PARTS == ("sub", "stab", "arp", "pad", "reese")   # reese: a Serum bass from its notes (2026-11-07)
    try:
        remixbuild.pairs(["stab=PL Crusty Pluck [LCV]"], remixbuild.SERUM_PARTS, "serum_preset")   # a preset named for one run still works
    except remixbuild.BuildError:
        raise AssertionError("a named preset for one run must be accepted") from None


def test_a_song_with_no_bass_line_hears_its_bass_against_the_other_stem(rig, ml, tmp_path):
    lib, stems, work, plan = _song(tmp_path)
    stems["bass"] = to_wav(str(tmp_path / "silent_bass.wav"), np.zeros(RATE))     # a guitar-and-voice song: nothing in the bass stem
    report: dict = {}
    remix_song.choose_sounds(_args("song_c", lib, tmp_path / "serum" / "serum_sounds.flp", "library"), plan, stems, "", work, {},
                             lambda label, module, **kw: rig.call(module, **kw), report)
    assert report["sounds"]["bass"]["heard_against"] == "other.wav" and json.loads(plan.read_text())["bass_sample"]["root_midi"] == 33
