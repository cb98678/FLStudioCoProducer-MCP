import struct

import numpy as np
import soundfile as sf

from coproducer import flpfile as F
from coproducer import testflp


def _render_and_project(tmp_path):
    rate, bar = 48000, 2.0  # 120 BPM: a bar is 2 s
    t = np.arange(int(4 * bar * rate)) / rate
    x = 0.05 * np.sin(2 * np.pi * 220 * t)
    x[int(2 * bar * rate) :] *= 8  # bars 3 and 4 are 18 dB louder: the drop
    sf.write(str(tmp_path / "r.wav"), x, rate)
    f = testflp.project({0: "Kick"}, {0: [0]}, bpm=120.0, bars=4)
    pl = f.current_arrangement()["playlist"]
    f.events[pl + 1 : pl + 1] = [[148, struct.pack("<I", 0)], [205, F.enc16("Build")], [148, struct.pack("<I", 2 * 384)], [205, F.enc16("Drop")]]
    f.save(str(tmp_path / "p.flp"))
    return str(tmp_path / "r.wav"), str(tmp_path / "p.flp")


def test_sections_from_markers_and_bars(rig, tmp_path):
    wav, proj = _render_and_project(tmp_path)
    r = rig.call("measure_section_levels", path=wav, project=proj).value
    build, drop = r["sections"]
    assert build["section"] == "Build" and drop["section"] == "Drop" and 16 < drop["lufs"] - build["lufs"] < 20
    bars = rig.call("measure_section_levels", path=wav, project=proj, sections=[{"name": "A", "start_bar": 1, "end_bar": 3}]).value
    assert bars["sections"][0]["end_s"] == 4.0
    no_project = rig.call("measure_section_levels", path=wav, sections=[{"name": "Build", "start_bar": 1, "end_bar": 3},
                                                                       {"name": "Drop", "start_bar": 3, "end_bar": 5}], bpm=120.0).value
    assert [r["section"] for r in no_project["sections"]] == ["Build", "Drop"] and no_project["contrast"]   # the panel's way: tempo from the plan


def test_failures(rig, tmp_path):
    wav, proj = _render_and_project(tmp_path)
    assert rig.call("measure_section_levels", path=str(tmp_path / "none.wav"), project=proj).error.code == "E_IO"
    assert rig.call("measure_section_levels", path=wav).error.code == "E_ARG"
    assert rig.call("measure_section_levels", path=wav, sections=[{"name": "A", "start_bar": 1, "end_bar": 2}]).error.code == "E_ARG"
