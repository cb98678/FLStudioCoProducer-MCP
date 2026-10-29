
import numpy as np
import soundfile as sf

from coproducer import flpfile, partmix
from coproducer.testflp import project, with_mixer


def _rig(tmp_path):
    f = project({0: "Kick", 1: "Chord Stab"}, {0: [0], 1: [0]})
    f.set_track(0, 1)
    f.set_track(1, 2)
    src = str(tmp_path / "mix.flp")
    with_mixer(f).save(src)
    solo, render = tmp_path / "solo", tmp_path / "render"
    man = partmix.split_to_dir(src, str(solo))
    render.mkdir()
    for (t, m), amp in zip(sorted(man["tracks"].items()), (0.4, 0.025)):      # stab is 24 dB under the kick
        x = amp * np.sin(2 * np.pi * 220 * np.arange(48000 * 3) / 48000)
        sf.write(render / (m["name"] + ".wav"), np.column_stack([x, x]), 48000)
    return src, str(solo), str(render)


def test_plans_and_applies(rig, desk, tmp_path):
    src, solo, render = _rig(tmp_path)
    prof = {"reference": "kick", "relative_db": {"stab": -12.0}}
    dry = rig.call("compare_part_levels", project=src, solo_dir=solo, render_dir=render, profile=prof)
    assert dry.ok and dry.value["written"] is None and [c["track"] for c in dry.value["changes"]] == [2]
    assert 11 < dry.value["changes"][0]["role_delta_db"] <= 12
    out = str(tmp_path / "sandbox" / "levelled.flp")
    (tmp_path / "sandbox").mkdir()
    r = rig.call("compare_part_levels", project=src, solo_dir=solo, render_dir=render, profile=prof, out_project=out)
    assert r.ok and r.meta["verified"] and r.value["written"] == out
    c = r.value["changes"][0]
    assert c["clamped"] and c["new_db"] == 5.5          # +12 dB wanted, the fader stops at +5.6
    assert abs(partmix.faders_db(flpfile.Flp.load(out), [2])[2] - c["new_db"]) < 0.6
    some = rig.call("compare_part_levels", project=src, solo_dir=solo, render_dir=render, profile={"reference": "kick", "relative_db": {"stab": -20.0}}).value
    assert abs(some["changes"][0]["role_delta_db"] - 4.0) < 0.3 and not some["changes"][0]["clamped"]
    ok_prof = {"reference": "kick", "relative_db": {"stab": -24.0}}
    assert rig.call("compare_part_levels", project=src, solo_dir=solo, render_dir=render, profile=ok_prof).value["within_tolerance"]


def test_failures(rig, desk, tmp_path):
    src, solo, render = _rig(tmp_path)
    prof = {"reference": "kick", "relative_db": {"stab": -12.0}}
    assert rig.call("compare_part_levels", project=src, solo_dir=solo, render_dir=render, profile=prof, out_project="/elsewhere/x.flp").error.code == "E_SANDBOX_VIOLATION"
    assert rig.call("compare_part_levels", project=src, solo_dir=str(tmp_path / "none"), render_dir=render, profile=prof).error.code == "E_IO"
    assert rig.call("compare_part_levels", project=src, solo_dir=solo, render_dir=render).error.code == "E_ARG"
