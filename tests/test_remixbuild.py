import pytest

from coproducer import flpfile, remixbuild, remixplan, songplan
from coproducer.testflp import remix_inputs


@pytest.fixture
def inputs(tmp_path):
    songplan.apply(songplan.load("plans/friends_in_low_places.json"))
    return remix_inputs(tmp_path, remixplan.CHOPS, remixplan.ECHOED)


def test_builds_a_project_with_every_part(inputs, tmp_path):
    (tmp_path / "sandbox").mkdir()
    out = str(tmp_path / "sandbox" / "out.flp")
    rep = remixbuild.build(inputs["base"], inputs["sytrus"], inputs["audio"], out, log=lambda *a: None)
    f = flpfile.Flp.load(out)
    names = [f.channel_info(c)["name"] for c in f.channel_ids()]
    assert {"Kick", "Reese Bass", "Sub Bass", "Chord Stab", "Rising Arp", "Chop Hook", "Vocal 124 BPM", "FX Bed"} <= set(names)
    assert f.tempo() == 124.0 and rep["pattern_counts"]["Stabs"] > 0 and len(rep["vocal_clips"]) == 3
    assert len(f.audio_clips()) == 4                      # three vocal clips and the FX bed
    marks = [(m["pos"] // 384, m["name"]) for m in f.time_markers()]  # the plan's sections as time markers, repeats numbered
    assert marks[:5] == [(0, "Intro"), (8, "Groove"), (24, "Break 1"), (32, "Build 1"), (40, "Drop 1")] and rep["markers"][-1] == "Outro"


def test_a_plan_changes_the_build(inputs, tmp_path):
    plan = songplan.load("plans/friends_in_low_places.json")
    plan["bpm"], plan["source_bpm"] = 128.0, 100.0
    plan["sections"] = [{"name": "intro", "start": 0, "end": 8}, {"name": "groove", "start": 8, "end": 24}, {"name": "build", "start": 24, "end": 32},
                        {"name": "drop", "start": 32, "end": 48}, {"name": "outro", "start": 48, "end": 56}]
    plan.pop("chop_events")
    plan.pop("fx_cues")
    songplan.apply(plan)
    (tmp_path / "sandbox").mkdir()
    out = str(tmp_path / "sandbox" / "o128.flp")
    remixbuild.build(inputs["base"], inputs["sytrus"], inputs["audio"], out, log=lambda *a: None)
    f = flpfile.Flp.load(out)
    assert f.tempo() == 128.0
    assert max(t for c in f.channel_ids() for t in f.note_ticks(c)) < 56 * flpfile.TICKS_PER_BAR
    assert "Vocal 128 BPM" in [f.channel_info(c)["name"] for c in f.channel_ids()]


def test_refusals(inputs, tmp_path):
    with pytest.raises(remixbuild.BuildError):
        remixbuild.build(inputs["base"], inputs["sytrus"], inputs["audio"], str(tmp_path / "elsewhere" / "o.flp"))
    with pytest.raises(remixbuild.BuildError):
        remixbuild.build(inputs["base"], inputs["sytrus"], inputs["audio"], str(tmp_path / "sandbox" / "o.flp"), kit=["nope=x.wav"])
    with pytest.raises(remixbuild.BuildError):
        remixbuild.build(inputs["base"], inputs["sytrus"], inputs["audio"], str(tmp_path / "sandbox" / "o.flp"), serum_db=["sub"])


def test_fl_stretch_sets_the_channel_and_keeps_the_windows_in_the_files_own_ms(inputs, tmp_path):
    """A plan with "vocal_stretch": "fl": the vocal file is at its own speed, the channel gets FL's stretch (TIME in 1/192 beat, so the file's
    own beats, e3 Mono) and each clip's content window stays in the file's milliseconds while its playlist length is the stretched one."""
    import json
    import struct
    import wave
    from pathlib import Path
    audio = Path(inputs["audio"])
    meta = json.loads((audio / "techhouse_audio.json").read_text(encoding="utf-8"))
    meta["fl_stretch"] = {"ratio": meta["stretch"], "modes": {"vocals": "stretch", "other": "e3_generic"}, "pitch_cents": {"vocals": -7}}
    (audio / "techhouse_audio.json").write_text(json.dumps(meta), encoding="utf-8")
    with wave.open(str(audio / ("vocals_%d.wav" % round(remixplan.BPM))), "wb") as w:   # two seconds of silence at the voice's own speed
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes(struct.pack("<%dh" % 88200, *([0] * 88200)))
    (tmp_path / "sandbox").mkdir()
    out = str(tmp_path / "sandbox" / "fl.flp")
    rep = remixbuild.build(inputs["base"], inputs["sytrus"], inputs["audio"], out, log=lambda *a: None)
    f = flpfile.Flp.load(out)
    st = f.stretch_settings(rep["channel_ids"]["vocal"])
    assert st["mode"] == "stretch" and st["pitch"] == -7 and abs(st["beats"] - 2.0 * remixplan.SOURCE_BPM / 60.0) < 1e-6
    assert f.stretch_settings(rep["channel_ids"]["fx"])["mode"] == "resample"      # only the stretched stems' channels
    ratio = float(meta["stretch"])
    for (pos, length, w0, w1), clip in zip(rep["vocal_clips"], meta["clips"]):
        assert abs(w0 - clip["orig_start_s"] * 1000.0) < 1e-6 and abs(w1 - clip["orig_end_s"] * 1000.0) < 1e-6   # the file's own ms
        assert abs(length - round((w1 - w0) / 1000.0 / ratio / (60.0 / remixplan.BPM / flpfile.TICKS_PER_BEAT))) <= 1   # its stretched length
