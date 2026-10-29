import numpy as np
from PIL import Image

from coproducer.services import set_service


def _pic(tmp_path, name, arr):
    Image.fromarray(arr.astype("uint8")).save(tmp_path / name)


def _setup(tmp_path, places):
    rng = np.random.default_rng(1)
    tpl = rng.integers(0, 255, (12, 30))
    img = np.full((120, 200), 60) + rng.integers(0, 4, (120, 200))
    for (r, c) in places:
        img[r:r + 12, c:c + 30] = tpl
    (tmp_path / "tpl").mkdir(exist_ok=True)
    _pic(tmp_path / "tpl", "item.png", tpl)
    _pic(tmp_path, "shot.png", img)
    set_service("templates_dir", str(tmp_path / "tpl"))


def test_finds_the_template_centre(rig, tmp_path):
    _setup(tmp_path, [(40, 70)])
    r = rig.call("locate_template", image_path=str(tmp_path / "shot.png"), template_name="item")
    assert r.ok and (r.value["x"], r.value["y"]) == (85, 46) and r.value["score"] > 0.99


def test_refuses_missing_absent_and_ambiguous(rig, tmp_path):
    _setup(tmp_path, [(40, 70)])
    assert rig.call("locate_template", image_path=str(tmp_path / "shot.png"), template_name="nope").error.code == "E_NOT_FOUND"
    _setup(tmp_path, [])
    assert rig.call("locate_template", image_path=str(tmp_path / "shot.png"), template_name="item").error.code == "E_GUI_MISMATCH"
    _setup(tmp_path, [(10, 10), (80, 120)])
    r = rig.call("locate_template", image_path=str(tmp_path / "shot.png"), template_name="item")
    assert r.error.code == "E_GUI_MISMATCH" and "more than one" in r.error.message
