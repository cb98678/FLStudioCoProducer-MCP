"""G2-3: every module that writes a file refuses a destination outside the sandbox, and nothing lands there."""
from __future__ import annotations

import pytest

from coproducer import fuzz

# module -> the argument that names where it writes
WRITERS = {
    "write_midi_file": "path", "prepare_rate_copy": "out_path", "prepare_stems_project": "out_project", "write_report_file": "path", "build_ab_package": "out_dir", "take_screenshot": "out_path",
    "save_project_copy": "path", "render_via_cli": "out_dir", "render_with_restart": "out_dir", "generate_audio": "out_dir",
    "generate_cover": "out_dir", "repaint_section": "out_dir", "separate_stems": "out_dir", "save_sandbox_project": "project",
    "export_split_stems_gui": "path", "transcribe_to_midi": "out_midi_path", "add_automation_clip": "project", "remove_automation_clip": "project",
    "build_remix_project": "out_project", "build_song_plan": "out_plan", "apply_project_standard": "out_project", "apply_effect_from_library": "out_project", "build_volume_pump": "out_project", "add_section_markers": "out_project", "add_transition_automation": "out_project", "build_layer_channel": "out_project", "apply_drum_tuning": "out_project", "add_transition_synths": "out_project", "apply_section_gains": "out_project", "create_bus_routing": "out_project", "apply_fx_chain": "out_project", "apply_production_recipe": "out_project", "split_part_projects": "out_dir", "compare_part_levels": "out_project",
    "apply_club_master": "out_path", "prepare_remix_audio": "out_dir", "build_reference_profile": "out_file", "write_song_notes": "out_file", "extract_song_loops": "out_dir", "build_wavetable": "out_path", "prepare_sampler_sound": "out_path",
}
NAME_ONLY = {"write_notes_via_script": "name"}  # a file name, not a path: anything with a separator is refused


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    w = fuzz.build_world(tmp_path_factory.mktemp("world"))
    yield w
    fuzz.close_world(w)


def _args(w, name, target_arg, target):
    paths = {"path": str(w.root / "sandbox" / "tone.wav"), "project": str(w.root / "sandbox" / "song.flp"),
             "out_dir": str(w.root / "sandbox" / "out"), "outside": str(w.root / "canary" / "outside")}
    sch = w.reg.modules[name].input_schema
    kw = {k: fuzz.base_value(v, k, paths) for k, v in sch.get("properties", {}).items() if k in sch.get("required", []) or k == target_arg}
    kw[target_arg] = target
    return kw


def _escapes(w):
    root = w.root
    return [str(root / "canary" / "outside" / "x.out"), "../../escape", str(root / "sandbox" / ".." / "canary" / "outside" / "y")]


def test_every_writer_in_the_list_exists_and_the_list_is_complete(world):
    """A new module that writes files has to be added here, so it gets this test."""
    declared = {n for n, m in world.reg.modules.items() if m.side_effect in ("writes_files",)}
    covered = set(WRITERS) | set(NAME_ONLY) | {"copy_project_to_sandbox"}  # its destination is fixed; the source is read only
    assert declared <= covered, sorted(declared - covered)
    assert set(WRITERS) | set(NAME_ONLY) <= set(world.reg.modules)


@pytest.mark.parametrize("name,arg", sorted(WRITERS.items()))
def test_writer_refuses_a_destination_outside_the_sandbox(world, name, arg):
    before = fuzz.tree(world.root, ("sandbox", "scripts"))
    for target in _escapes(world):
        r = world.reg.call(name, **_args(world, name, arg, target))
        assert not r.ok and r.error.code == "E_SANDBOX_VIOLATION", (name, target, r)
    assert fuzz.tree(world.root, ("sandbox", "scripts")) == before


@pytest.mark.parametrize("name,arg", sorted(NAME_ONLY.items()))
def test_name_arguments_cannot_carry_a_path(world, name, arg):
    before = fuzz.tree(world.root, ("sandbox", "scripts"))
    for target in _escapes(world):
        r = world.reg.call(name, **_args(world, name, arg, target))
        assert not r.ok and r.error.code in ("E_ARG", "E_SANDBOX_VIOLATION"), (name, target, r)
    assert fuzz.tree(world.root, ("sandbox", "scripts")) == before
