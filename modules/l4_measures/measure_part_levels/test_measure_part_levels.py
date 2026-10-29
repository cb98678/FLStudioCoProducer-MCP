import json

import numpy as np
import soundfile as sf


def _setup(tmp_path, amps):
    solo, render = tmp_path / "solo", tmp_path / "render"
    solo.mkdir()
    render.mkdir()
    tracks = {str(t): {"name": "p__t%02d_%s" % (t, role), "role": role, "channels": [role]} for t, (role, _a) in enumerate(amps.items(), 1)}
    (solo / "manifest.json").write_text(json.dumps({"project": "p", "tracks": tracks}))
    for t, (role, a) in zip(tracks.values(), amps.items()):
        x = a[1] * np.sin(2 * np.pi * 220 * np.arange(48000 * 3) / 48000)
        sf.write(render / (t["name"] + ".wav"), np.column_stack([x, x]), 48000)
    return str(solo), str(render)


def test_measures_parts(rig, tmp_path):
    solo, render = _setup(tmp_path, {"kick": ("kick", 0.4), "stab": ("stab", 0.1)})
    r = rig.call("measure_part_levels", solo_dir=solo, render_dir=render).value
    assert [p["role"] for p in r["parts"]] == ["kick", "stab"] and r["missing"] == []
    assert abs(r["profile"]["relative_db"]["stab"] + 12.0) < 0.5 and r["profile"]["reference"] == "kick"
    (tmp_path / "render" / "p__t02_stab.wav").unlink()
    again = rig.call("measure_part_levels", solo_dir=solo, render_dir=render)
    assert again.ok and again.value["missing"] == ["p__t02_stab"]


def test_failures(rig, tmp_path):
    assert rig.call("measure_part_levels", solo_dir=str(tmp_path / "nope"), render_dir=str(tmp_path)).error.code == "E_IO"
    solo, render = _setup(tmp_path, {"stab": ("stab", 0.1)})
    assert rig.call("measure_part_levels", solo_dir=solo, render_dir=render).error.code == "E_IO"   # no kick, no reference
    assert rig.call("measure_part_levels", solo_dir="", render_dir="x").error.code == "E_ARG"
