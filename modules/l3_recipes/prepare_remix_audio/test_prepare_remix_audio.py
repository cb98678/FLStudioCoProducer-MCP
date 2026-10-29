import json

import numpy as np
import soundfile as sf

from coproducer import songplan
from coproducer.services import set_service


def _voice(path, seconds=150.0, rate=22050):
    """A sung-like test stem: 0.4 s vowels on a rising line with short gaps, so chops and phrases find onsets."""
    t = np.arange(int(seconds * rate)) / rate
    f = 180 + 40 * np.sin(2 * np.pi * 0.05 * t)
    env = ((t % 0.5) < 0.4).astype(float)
    x = 0.3 * env * (np.sin(2 * np.pi * np.cumsum(f) / rate) + 0.3 * np.sin(4 * np.pi * np.cumsum(f) / rate))
    sf.write(path, np.stack([x, x], 1).astype(np.float32), rate)
    return path


def test_writes_the_audio_of_a_styled_plan(rig, tmp_path):
    set_service("sandbox_root", str(tmp_path / "sandbox"))
    plan = songplan.load("plans/friends_in_low_places.json")
    plan.update(style="dubstep", bpm=140.0, vocal_multiple=1.0)
    pf = tmp_path / "sandbox" / "plan.json"
    pf.parent.mkdir()
    songplan.save(plan, pf)
    voc = _voice(str(tmp_path / "vocals.wav"))
    out = tmp_path / "sandbox" / "audio"
    try:
        r = rig.call("prepare_remix_audio", plan_file=str(pf), vocals_path=voc, out_dir=str(out))
    finally:
        songplan.apply(songplan.load("plans/friends_in_low_places.json"))
    assert r.ok and r.meta["verified"], r
    assert r.value["style"] == "dubstep" and abs(r.value["stretch"] - 140 / 108.478) < 1e-6
    assert (out / "vocals_140.wav").is_file() and (out / "CP_Reese.wav").is_file() and (out / "FX_bed.wav").is_file()
    meta = json.loads((out / "techhouse_audio.json").read_text())
    assert meta["style"] == "dubstep" and len(meta["chops"]) >= 10
    growl, rate = sf.read(str(out / "CP_Reese.wav"))
    assert growl.ndim == 2 and rate == 44100                  # the dubstep growl is stereo


def test_errors(rig, tmp_path):
    set_service("sandbox_root", str(tmp_path / "sandbox"))
    assert rig.call("prepare_remix_audio", plan_file="plans/friends_in_low_places.json", vocals_path="none.wav",
                    out_dir=str(tmp_path / "elsewhere")).error.code == "E_SANDBOX_VIOLATION"
    assert rig.call("prepare_remix_audio", plan_file="plans/friends_in_low_places.json", vocals_path=str(tmp_path / "none.wav"),
                    out_dir=str(tmp_path / "sandbox" / "a")).error.code == "E_NOT_FOUND"
