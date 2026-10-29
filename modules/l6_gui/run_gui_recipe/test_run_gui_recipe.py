import json

from coproducer.services import set_service


def make_recipe(tmp_path, steps, params=(), verified=True):
    (tmp_path / "recipes").mkdir(exist_ok=True)
    (tmp_path / "recipes" / "demo.json").write_text(json.dumps({"name": "demo", "verified": verified, "params": list(params), "steps": steps}))
    set_service("recipes_dir", str(tmp_path / "recipes"))


def test_runs_a_recipe_end_to_end(rig, desk, tmp_path):
    out = tmp_path / "saved.flp"
    desk.fake.script_dialog(("ctrl", "shift", "s"), "Save as", on_enter=lambda text: open(text, "wb").write(b"FLhd data"))
    make_recipe(tmp_path, [{"do": "hotkey", "keys": ["ctrl", "shift", "s"]}, {"do": "expect_dialog", "contains": "save"},
                           {"do": "type", "text": "{path}"}, {"do": "hotkey", "keys": ["enter"]}, {"do": "expect_no_dialog"},
                           {"do": "expect_file", "path": "{path}"}, {"do": "expect_title", "contains": "FL Studio"}], ["path"])
    r = rig.call("run_gui_recipe", name="demo", params={"path": str(out)})
    assert r.ok and r.value["steps_run"] == 7 and out.read_bytes() == b"FLhd data" and r.meta["unverified_recipe"] is False


def test_stops_and_explains(rig, desk, tmp_path):
    make_recipe(tmp_path, [{"do": "hotkey", "keys": ["f8"]}, {"do": "expect_dialog", "contains": "Nothing"}, {"do": "hotkey", "keys": ["f9"]}])
    r = rig.call("run_gui_recipe", name="demo")
    assert r.error.code == "E_GUI_MISMATCH" and r.error.detail["step"] == 2 and r.error.detail["screenshot"].endswith("failed_demo.png")
    assert ("hotkey", ("f9",)) not in desk.fake.log                         # nothing ran after the failure
    assert rig.call("run_gui_recipe", name="demo", params={}).error.code == "E_GUI_MISMATCH"
    make_recipe(tmp_path, [{"do": "wait", "seconds": 0.1}], ["path"])
    assert rig.call("run_gui_recipe", name="demo").error.code == "E_ARG"
    make_recipe(tmp_path, [{"do": "click", "anchor": "unset"}])
    assert rig.call("run_gui_recipe", name="demo").error.detail["kind"] == "click"
    make_recipe(tmp_path, [{"do": "wait", "seconds": 0.1}], verified=False)
    desk.cfg["allow_unverified"] = False
    assert rig.call("run_gui_recipe", name="demo").error.code == "E_UNSUPPORTED_API"
    desk.cfg["allow_unverified"] = True
    assert rig.call("run_gui_recipe", name="demo").meta["unverified_recipe"] is True
    desk.fake.open_dialog("Surprise")
    make_recipe(tmp_path, [{"do": "expect_no_dialog", "timeout_s": 1}])
    blocked = rig.call("run_gui_recipe", name="demo")
    assert blocked.error.code == "E_BLOCKED_BY_DIALOG"


def test_click_in_window_uses_the_found_window_position(rig, desk, tmp_path):
    desk.fake.open_dialog("Audio Clip (Master)")                           # the fake puts it at (100, 100)
    make_recipe(tmp_path, [{"do": "click_in_window", "title": "audio clip", "dx": 10, "dy": 20}])
    assert rig.call("run_gui_recipe", name="demo").ok
    assert ("click", 110, 120, "left", 1) in desk.fake.log
    make_recipe(tmp_path, [{"do": "click_in_window", "title": "No such window", "dx": 1, "dy": 1}])
    assert rig.call("run_gui_recipe", name="demo").error.code == "E_GUI_MISMATCH"


def test_click_row_moves_down_by_whole_rows(rig, desk, tmp_path):
    desk.cfg["anchors"] = {"row1": [10, 20]}
    make_recipe(tmp_path, [{"do": "click_row", "anchor": "row1", "param": "track", "dy": 48}], ["track"])
    assert rig.call("run_gui_recipe", name="demo", params={"track": 3}).ok
    assert ("click", 10, 116, "left", 1) in desk.fake.log
    make_recipe(tmp_path, [{"do": "click_row", "anchor": "nope", "param": "track", "dy": 48}], ["track"])
    assert rig.call("run_gui_recipe", name="demo", params={"track": 1}).error.code == "E_GUI_MISMATCH"


def test_a_recipe_that_needs_a_sandbox_project_refuses_others(rig, desk, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    make_recipe(tmp_path, [{"do": "hotkey", "keys": ["f9"]}])
    rec = json.loads((tmp_path / "recipes" / "demo.json").read_text())
    rec["needs_sandbox_project"] = True
    (tmp_path / "recipes" / "demo.json").write_text(json.dumps(rec))
    desk.fake.main["title"] = "mine.flp - FL Studio 2026"
    assert rig.call("run_gui_recipe", name="demo").error.code == "E_SANDBOX_VIOLATION"
    assert ("hotkey", ("f9",)) not in desk.fake.log
    (tmp_path / "mine.flp").write_bytes(b"FLhd")
    assert rig.call("run_gui_recipe", name="demo").ok


def test_a_sandbox_recipe_refuses_to_start_over_an_open_dialog(rig, desk, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    (tmp_path / "mine.flp").write_bytes(b"FLhd")
    desk.fake.main["title"] = "mine.flp - FL Studio 2026"
    make_recipe(tmp_path, [{"do": "hotkey", "keys": ["f9"]}])
    rec = json.loads((tmp_path / "recipes" / "demo.json").read_text())
    rec["needs_sandbox_project"] = True
    (tmp_path / "recipes" / "demo.json").write_text(json.dumps(rec))
    desk.fake.open_dialog("Open")
    r = rig.call("run_gui_recipe", name="demo")
    assert r.error.code == "E_BLOCKED_BY_DIALOG" and ("hotkey", ("f9",)) not in desk.fake.log


def test_template_click_finds_the_picture_on_the_screenshot(rig, desk, tmp_path):
    import numpy as np
    from PIL import Image
    tpl = np.random.default_rng(3).integers(0, 255, (10, 24)).astype("uint8")
    (tmp_path / "tpl").mkdir()
    Image.fromarray(tpl).save(tmp_path / "tpl" / "item.png")
    set_service("templates_dir", str(tmp_path / "tpl"))
    set_service("sandbox_root", str(tmp_path))
    plain = desk.fake.grab

    def grab(rect):
        arr = plain(rect)
        arr[50:60, 100:124, :] = tpl[:, :, None]
        return arr
    desk.fake.grab = grab
    make_recipe(tmp_path, [{"do": "template_click", "template": "item"}])
    assert rig.call("run_gui_recipe", name="demo").ok
    assert ("click", 112, 55, "left", 1) in desk.fake.log
    make_recipe(tmp_path, [{"do": "template_click", "template": "gone"}])
    assert rig.call("run_gui_recipe", name="demo").error.code == "E_NOT_FOUND"


def test_template_name_takes_recipe_parameters(rig, desk, tmp_path):
    import numpy as np
    from PIL import Image
    tpl = np.random.default_rng(5).integers(0, 255, (10, 24)).astype("uint8")
    (tmp_path / "tpl").mkdir()
    Image.fromarray(tpl).save(tmp_path / "tpl" / "pr_script_mine.png")
    set_service("templates_dir", str(tmp_path / "tpl"))
    set_service("sandbox_root", str(tmp_path))
    plain = desk.fake.grab

    def grab(rect):
        arr = plain(rect)
        arr[50:60, 100:124, :] = tpl[:, :, None]
        return arr
    desk.fake.grab = grab
    make_recipe(tmp_path, [{"do": "template_click", "template": "pr_script_{script}"}], params=["script"])
    assert rig.call("run_gui_recipe", name="demo", params={"script": "mine"}).ok
    assert ("click", 112, 55, "left", 1) in desk.fake.log


def test_click_col_moves_right_by_whole_columns_and_can_right_click(rig, desk, tmp_path):
    desk.cfg["anchors"] = {"strip1": [10, 20]}
    make_recipe(tmp_path, [{"do": "click_col", "anchor": "strip1", "param": "n", "dx": 42, "button": "right"}], ["n"])
    assert rig.call("run_gui_recipe", name="demo", params={"n": 3}).ok
    assert ("click", 94, 20, "right", 1) in desk.fake.log


def test_click_in_window_can_step_down_by_a_parameter_and_right_click(rig, desk, tmp_path):
    desk.fake.open_dialog("Fruity Limiter (Insert 2)")                     # the fake puts it at (100, 100)
    make_recipe(tmp_path, [{"do": "click_in_window", "title": "(Insert {dest})", "dx": 5, "dy": 10, "param": "k", "dy_each": 19, "button": "right"}], ["dest", "k"])
    assert rig.call("run_gui_recipe", name="demo", params={"dest": 2, "k": 3}).ok
    assert ("click", 105, 148, "right", 1) in desk.fake.log


def test_expect_dialog_can_name_a_parameter(rig, desk, tmp_path):
    """load_plugin_gui ends by waiting for the plugin's own window, whose title carries the plugin name."""
    desk.fake.open_dialog("Fruity Limiter (Master)")
    make_recipe(tmp_path, [{"do": "expect_dialog", "contains": "{name}", "timeout_s": 1}], ["name"])
    assert rig.call("run_gui_recipe", name="demo", params={"name": "Fruity Limiter"}).ok
    missing = rig.call("run_gui_recipe", name="demo", params={"name": "Sytrus"})
    assert missing.error.code == "E_GUI_MISMATCH" and "Sytrus" in missing.error.message
