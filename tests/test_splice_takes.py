"""tools/splice_takes.py: one stem from aligned takes, chosen by region, the editor's lead-in trimmed."""
import importlib.util
from pathlib import Path

import numpy as np
import soundfile as sf

spec = importlib.util.spec_from_file_location("splice_takes", Path(__file__).resolve().parents[1] / "tools" / "splice_takes.py")
st = importlib.util.module_from_spec(spec)
spec.loader.exec_module(st)


def test_regions_take_their_take_and_the_lead_in_is_trimmed(tmp_path):
    rate = 1000
    a, b = np.full((3000, 1), 0.1, "float32"), np.full((3000, 1), 0.5, "float32")
    sf.write(str(tmp_path / "a.wav"), a, rate)
    sf.write(str(tmp_path / "b.wav"), b, rate)
    y, r = st.splice({"a": str(tmp_path / "a.wav"), "b": str(tmp_path / "b.wav")}, "a", [(1.0, 2.0, "b")], trim_s=0.5, xfade_s=0.01)
    assert r == rate and len(y) == 2500
    assert abs(y[500, 0] - 0.1) < 1e-4 and abs(y[1500, 0] - 0.5) < 1e-3 and abs(y[2200, 0] - 0.1) < 1e-4
