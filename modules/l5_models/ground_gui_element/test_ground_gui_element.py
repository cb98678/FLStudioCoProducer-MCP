def shot(tmp_path):
    f = tmp_path / "s.png"
    f.write_bytes(b"png")
    return str(f)


def test_finds_an_element_and_applies_the_confidence_floor(rig, ml, tmp_path, monkeypatch):
    r = rig.call("ground_gui_element", image_path=shot(tmp_path), description="play button")
    assert r.ok and (r.value["x"], r.value["y"]) == (10, 20)
    assert rig.call("ground_gui_element", image_path=shot(tmp_path), description="play button", min_confidence=0.95).error.code == "E_GUI_MISMATCH"


def test_missing_screenshot_and_model_not_configured(rig, ml, tmp_path, monkeypatch):
    assert rig.call("ground_gui_element", image_path=str(tmp_path / "no.png"), description="play button").error.code == "E_NOT_FOUND"
    monkeypatch.setenv("FAKE_GROUND_FAIL", "1")
    ml.sched.unload_all()
    r = rig.call("ground_gui_element", image_path=shot(tmp_path), description="play button")
    assert r.error.code == "E_MODEL" and "grounding model" in r.error.message
