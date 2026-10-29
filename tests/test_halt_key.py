"""G2-5: the halt key and `coproducer halt` stop a GUI recipe at the next action, and a person clears it."""
from __future__ import annotations

import json

import pytest

from coproducer import halt_key
from coproducer.cli import build_parser, dispatch
from coproducer.services import set_service
from coproducer.wiring import FileHalt


def test_trip_writes_the_global_file_and_every_run_sees_it(tmp_path):
    a, b = FileHalt(tmp_path / "runs" / "one"), FileHalt(tmp_path / "runs" / "two")
    assert not a.is_set() and not b.is_set()
    halt_key.trip(tmp_path, "halt key pressed")
    assert a.is_set() and b.is_set()
    assert halt_key.clear(tmp_path) is True and not a.is_set() and not b.is_set()
    assert halt_key.clear(tmp_path) is False


def test_clear_also_removes_a_runs_own_halt_file(tmp_path):
    (tmp_path / "runs" / "r1").mkdir(parents=True)
    (tmp_path / "runs" / "r1" / "HALT").write_text("x")
    assert halt_key.clear(tmp_path) is True and not (tmp_path / "runs" / "r1" / "HALT").exists()


def test_a_recipe_stops_at_the_next_action_when_halted_in_the_middle(rig, desk, tmp_path):
    """The halt arrives while the recipe is running (after its second action): nothing after that action is sent."""
    recipes = tmp_path / "recipes"
    recipes.mkdir()
    steps = [{"do": "hotkey", "keys": [k]} for k in ("f1", "f2", "f3", "f4", "f5")]
    (recipes / "demo.json").write_text(json.dumps({"name": "demo", "verified": True, "params": [], "steps": steps}))
    set_service("recipes_dir", str(recipes))
    set_service("halt", FileHalt(tmp_path / "runs" / "r1"))
    sent = []
    orig_log = desk.fake.log

    class Watch(list):
        def append(self, item):
            super().append(item)
            sent.append(item)
            if len(sent) == 2:
                halt_key.trip(tmp_path, "halt key pressed")
    desk.fake.log = Watch(orig_log)
    r = rig.call("run_gui_recipe", name="demo")
    assert not r.ok and r.error.code == "E_HALTED", r
    keys = [i for i in sent if i and i[0] == "hotkey"]
    assert len(keys) == 2, keys            # f3, f4 and f5 were never sent


def test_cli_halt_and_clear(tmp_path, capsys):
    assert dispatch(build_parser().parse_args(["--home", str(tmp_path), "halt"])) == 0
    assert (tmp_path / "runs" / "HALT").exists()
    assert dispatch(build_parser().parse_args(["--home", str(tmp_path), "halt", "--clear"])) == 0
    assert not (tmp_path / "runs" / "HALT").exists()
    assert "cleared" in capsys.readouterr().out


def test_listener_refuses_to_run_off_windows(tmp_path):
    import sys
    if sys.platform == "win32":
        pytest.skip("needs a non-Windows machine")
    with pytest.raises(OSError):
        halt_key.listen(tmp_path)
