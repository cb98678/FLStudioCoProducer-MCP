"""An original track with no source song (instrumental.draft_plan, the person's ask of 2026-11-07): a plan with no vocal, the parts written
for it in true MIDI, and a build with no vocal channel."""
import json

import pytest

from coproducer import flpfile, instrumental, remixbuild, remixplan, songplan
from coproducer.testflp import remix_inputs

BASS = [[0, 0.5, 41, 120], [0.5, 0.5, 41, 100], [4, 1.5, 41, 120], [5.5, 0.5, 44, 100]]       # F2, Ab2
SUB = [[0, 2, 29, 112], [2, 1, 29, 104], [3, 1, 32, 104]]                                      # F1, Ab1
PAD = [[0, 8, 53, 90], [0, 8, 56, 90], [0, 8, 60, 90]]                                         # F minor
LEAD = [[0, 1, 65, 108], [1, 0.5, 68, 100], [1.5, 1.5, 72, 112]]


@pytest.fixture
def restore():
    saved = songplan.export_current()
    yield
    songplan.apply(saved)


def _midi(path, rows):
    import mido
    m = mido.MidiFile(ticks_per_beat=96)
    t = mido.MidiTrack()
    m.tracks.append(t)
    evs = []
    for st, d, p, v in rows:
        evs += [(int(st * 96), "note_on", p, v), (int((st + d) * 96), "note_off", p, 0)]
    tick = 0
    for at, kind, p, v in sorted(evs, key=lambda e: (e[0], e[1] == "note_on")):
        t.append(mido.Message(kind, note=p, velocity=v, time=at - tick))
        tick = at
    m.save(str(path))


def test_draft_is_a_valid_plan_with_no_vocal(tmp_path):
    _midi(tmp_path / "bass.mid", BASS)
    plan = instrumental.draft_plan("orig", style="dubstep", key_pc=5, mode="minor", chords=["Fm", "Db", "Ab", "Eb"],
                                   part_files={"bass": str(tmp_path / "bass.mid")}, part_notes={"sub": SUB, "pad": PAD, "lead": LEAD}, omit=["stab"])
    assert songplan.validate(plan) == []
    assert plan["roots8"] == [5, 5, 1, 1, 8, 8, 3, 3] and plan["root_quality"] == {"5": "min"}
    assert plan["instrumental"] and plan["chops"] == {} and plan["vocal_clips"] == [] and plan["chop_events"] == []
    assert plan["bpm"] == plan["source_bpm"] == 140.0 and plan["style"] == "dubstep" and plan["pattern_bars"] == 16
    assert [s["name"] for s in plan["sections"]][:3] == ["intro", "build", "drop"] and plan["sections"][-1]["end"] == 88
    assert plan["part_notes"]["bass"] == [[0.0, 0.5, 41, 120], [0.5, 0.5, 41, 100], [4.0, 1.5, 41, 120], [5.5, 0.5, 44, 100]]
    both = instrumental.part_files_notes([str(tmp_path / "bass.mid") + "@24", str(tmp_path / "bass.mid") + "@64"])   # drop 1 and drop 2
    assert [n[0] for n in both] == [96.0, 96.5, 100.0, 101.5, 256.0, 256.5, 260.0, 261.5]
    assert plan["omit_parts"] == ["stab"] and plan["fx_cues"] and "no vocal" in plan["notes"][0]


def test_draft_refuses_bad_parts(tmp_path):
    with pytest.raises(ValueError):
        instrumental.draft_plan("orig", style="dubstep", key_pc=5, part_notes={"guitar": LEAD})
    with pytest.raises(ValueError):
        instrumental.draft_plan("orig", style="dubstep", key_pc=5, chords=["Fm", "H"])
    with pytest.raises(ValueError):
        instrumental.draft_plan("orig", style="dubstep", key_pc=5, part_notes={"lead": [[0, 1, 200, 100]]})
    with pytest.raises(ValueError):
        instrumental.draft_plan("orig", style="dubstep", key_pc=5, sections=[["intro", 4]], part_notes={"lead": [[64, 1, 65, 100]]})   # past the end
    plan = instrumental.draft_plan("orig", style="dubstep", key_pc=5)
    plan["part_notes"] = {"bass": [[0, 1, 41]]}
    assert any("part_notes" in p for p in songplan.validate(plan))
    plan["part_notes"], plan["omit_parts"] = {}, ["drums"]
    assert any("omit_parts" in p for p in songplan.validate(plan))


def test_parts_land_on_their_channels_in_the_right_key_space(restore):
    plan = instrumental.draft_plan("orig", style="dubstep", key_pc=5, part_notes={"bass": BASS, "sub": SUB, "pad": PAD, "lead": LEAD}, omit=["stab"])
    songplan.apply(plan)
    reese = remixplan.reese_notes()
    assert [n[2] for n in reese] == [60 + 41 - 33, 60 + 41 - 33, 60 + 41 - 33, 60 + 44 - 33]   # the bass sampler's key 60 is A1
    sub = remixplan.sub_notes(remixplan.drums())
    assert sub and all(n[2] in (29 + 7, 32 + 7) for n in sub)                                   # the Remix Sub patch wants MIDI + 7
    assert [n[2] for n in remixplan.pad_notes()] == [53, 56, 60] and [n[2] for n in remixplan.arp_notes()] == [65, 68, 72]
    assert remixplan.stab_notes() == []                                                          # omitted
    assert remixplan.chop_events() == [] and remixplan.fx_cues()


def test_build_writes_no_vocal_channel(restore, tmp_path):
    plan = instrumental.draft_plan("orig", style="dubstep", key_pc=5, part_notes={"bass": BASS, "sub": SUB, "pad": PAD, "lead": LEAD, "keys": BASS},
                                   labels={"keys": "Bass - Second Line"})   # a second bass on the stab channel, named as a bass
    songplan.apply(plan)
    inputs = remix_inputs(tmp_path, {}, ())
    meta = {"stretch": 1.0, "delay_s": 0.0, "chops": {}, "clips": [], "instrumental": True}
    (tmp_path / "audio" / "techhouse_audio.json").write_text(json.dumps(meta), encoding="utf-8")
    (tmp_path / "sandbox").mkdir()
    out = str(tmp_path / "sandbox" / "orig.flp")
    rep = remixbuild.build(inputs["base"], inputs["sytrus"], inputs["audio"], out, log=lambda *a: None)
    f = flpfile.Flp.load(out)
    names = [f.channel_info(c)["name"] for c in f.channel_ids()]
    assert not any(n.lower().startswith("vocal") for n in names) and not any(n.startswith("Chop") for n in names)
    assert {"Kick", "Growl Bass", "Sub Bass", "Pad", "Lead", "FX Bed", "Bass - Second Line"} <= set(names) and "Chord Stab" not in names
    assert len(f.audio_clips()) == 1 and rep["vocal_clips"] == [] and rep["pattern_counts"]["Reese"] > 0 and rep["pattern_counts"]["Arp"] > 0
    assert f.tempo() == 140.0 and rep["markers"][0] == "Intro" and rep["markers"][-1] == "Outro"
