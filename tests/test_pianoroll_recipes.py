import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "src" / "coproducer" / "data"


def test_piano_roll_recipes_never_press_the_toggle_key_and_have_their_templates():
    arm = json.loads((DATA / "gui_recipes" / "arm_piano_roll_script_gui.json").read_text())
    assert not any(s.get("keys") == ["f7"] for s in arm["steps"])
    assert (DATA / "gui_templates" / "piano_roll_wrench.png").is_file()
    assert (DATA / "gui_templates" / "pr_script_coproducer_notes.png").is_file()
    run = json.loads((DATA / "gui_recipes" / "run_piano_roll_script_gui.json").read_text())
    assert run["steps"][0]["do"] == "click_in_window" and run["steps"][-1]["do"] == "expect_no_dialog"


def test_sidechain_recipes_have_their_template_and_anchors_named():
    send = json.loads((DATA / "gui_recipes" / "set_sidechain_send_gui.json").read_text())
    assert (DATA / "gui_templates" / "mixer_sidechain_menu_item.png").is_file()
    assert {s.get("anchor") for s in send["steps"] if s["do"] == "click_col"} == {"mixer_strip1_name", "mixer_send1_switch"}
    assert send["needs_sandbox_project"] is True
