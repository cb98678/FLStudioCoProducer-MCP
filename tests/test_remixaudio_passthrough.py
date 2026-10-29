import shutil

import numpy as np
import pytest
import soundfile as sf

from coproducer import remixaudio


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
def test_a_stretch_of_one_copies_the_voice_untouched(tmp_path):
    rate = 44100
    t = np.arange(rate) / rate
    x = (0.3 * np.sin(2 * np.pi * 220 * t) * np.minimum(1, t * 20)).astype("float32")
    src = tmp_path / "v.wav"
    sf.write(str(src), np.stack([x, x], axis=1), rate, subtype="FLOAT")
    remixaudio.stretch(str(src), tmp_path / "same.wav", 1.0, 1.0)
    y, r = sf.read(str(tmp_path / "same.wav"))
    assert r == rate and len(y) == len(x) and np.max(np.abs(y[:, 0] - x)) < 1e-4      # 16-bit rounding only, no phase vocoder
