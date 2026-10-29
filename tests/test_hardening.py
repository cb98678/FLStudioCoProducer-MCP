"""Defects the fuzzer found, pinned so they stay fixed."""

import pytest



def test_registry_refuses_nan_infinity_nul_and_lone_surrogates_in_any_argument(rig):
    for bad in (float("nan"), float("inf"), "a\x00b", "\ud83d"):
        r = rig.call("wait_for_reply", req_id=1, timeout_s=bad) if isinstance(bad, float) else rig.call("check_sandbox_path", path=bad, sandbox_root="/x")
        assert not r.ok and r.error.code == "E_ARG", repr(bad)


def test_nested_bad_text_is_found_too(rig):
    r = rig.call("set_rough_balance", levels_db={"1\x00": -3})
    assert not r.ok and r.error.code == "E_ARG"


def test_wait_for_reply_cannot_be_asked_to_wait_forever(rig):
    r = rig.call("wait_for_reply", req_id=1, timeout_s=1e9)
    assert not r.ok and r.error.code == "E_ARG"


def test_a_whole_float_is_accepted_for_an_integer_argument(rig):
    r = rig.call("list_tracks_summary", start=1.0, count=2.0)
    assert r.ok or r.error.code != "E_INTERNAL"


def test_an_unguarded_os_error_becomes_e_io_not_a_crash(rig):
    r = rig.call("check_sandbox_path", path="a" * 5000, sandbox_root="/tmp")
    assert not r.ok and r.error.code in ("E_IO", "E_SANDBOX_VIOLATION", "E_ARG")


def test_fl_range_errors_are_argument_errors(rig):
    r = rig.call("op_mixer_set_current_tempo", tempo=0)
    assert not r.ok and r.error.code == "E_ARG"


@pytest.mark.parametrize("name,args", [("set_rough_balance", {"levels_db": {"x": -3}}), ("restore_solo_group", {"previous": {"x": True}}),
                                       ("restore_solo_group", {"previous": {"1": "yes"}})])
def test_index_maps_refuse_keys_and_values_that_are_not_indexes(rig, name, args):
    r = rig.call(name, **args)
    assert not r.ok and r.error.code == "E_ARG"


def test_toml_loaders_survive_a_file_that_is_not_text(rig, tmp_path):
    f = tmp_path / "x.toml"
    f.write_bytes(b"\xff\xfe\x98\x00binary")
    for name in ("load_genre_profile", "load_invariants_file", "load_targets_file"):
        r = rig.call(name, path=str(f))
        assert not r.ok and r.error.code == "E_IO", name


def test_bridge_client_is_safe_from_many_threads(rig):
    import threading
    bad = []

    def work():
        for _ in range(30):
            r = rig.client.ping()
            if not r.ok:
                bad.append(r.error.code)

    ts = [threading.Thread(target=work) for _ in range(6)]
    [t.start() for t in ts]
    [t.join(60) for t in ts]
    assert not bad


def test_read_audio_file_cannot_be_asked_for_an_absurd_length(rig, tmp_path):
    r = rig.call("read_audio_file", path=str(tmp_path / "x.wav"), max_seconds=1e308)
    assert not r.ok and r.error.code == "E_ARG"


@pytest.mark.parametrize("bad", ["CON", "nul", "aux.txt", "COM1.wav", "a/b/LPT2", "C:\\x\\PRN.wav", "CON .txt", "\\\\server\\share\\x", "//host/x", "\\\\?\\C:\\x",
                                 "\\\\.\\pipe\\x", "C:\\a:stream", "con:", "COM\u00b9.txt", "LPT\u00b3"])
def test_windows_device_names_and_network_paths_are_refused_in_path_arguments(rig, bad):
    r = rig.call("check_sandbox_path", path=bad, sandbox_root="/x")
    assert not r.ok and r.error.code == "E_ARG", bad


@pytest.mark.parametrize("good", ["/tmp/a.wav", "C:\\ok\\file.wav", "relative/p.wav", "console.txt", "D:/music/song.wav", "sandbox/out/c.wav", "LPT10"])
def test_ordinary_paths_still_pass_the_guard(good):
    from coproducer.schema import unsafe_path
    assert unsafe_path(good) == ""


def test_the_guard_only_looks_at_arguments_named_like_paths(rig):
    r = rig.call("find_track_by_name", name="CON")
    assert r.ok or r.error.code != "E_ARG" or "device" not in r.error.message


def test_every_string_argument_that_names_a_file_is_guarded():
    """If a new module adds a path argument with an unusual name, this lists it so it can be added to the guard."""
    from coproducer.registry import Registry
    from coproducer.schema import is_path_name
    from coproducer.testrig import MODULES
    reg = Registry(MODULES).load(lint=False)
    fileish = ("path", "dir", "folder", "file", "project", "src", "dest", "target", "output", "input")
    missed = sorted({"%s.%s" % (m.name, k) for m in reg.modules.values() for k, v in (m.input_schema.get("properties") or {}).items()
                     if v.get("type") == "string" and any(w in k.lower() for w in fileish) and not is_path_name(k) and not v.get("x-path") and k not in ("target", "prompt", "input_text")})
    for mod, prop in (("copy_project_to_sandbox", "source"), ("write_notes_via_script", "name"), ("load_gui_recipe", "name"), ("run_gui_recipe", "name"),
                      ("locate_template", "template_name")):
        assert reg.modules[mod].input_schema["properties"][prop].get("x-path") is True, (mod, prop)
    assert not missed, missed


@pytest.mark.parametrize("mod,args", [("load_gui_recipe", {"name": "CON"}), ("run_gui_recipe", {"name": "NUL"}), ("write_notes_via_script", {"name": "aux", "notes": []}),
                                      ("copy_project_to_sandbox", {"source": "\\\\server\\share\\x.flp"}), ("locate_template", {"template_name": "con.png", "screenshot_path": "x"})])
def test_arguments_that_become_file_names_are_guarded_too(rig, mod, args):
    r = rig.call(mod, **args)
    assert not r.ok and r.error.code == "E_ARG" and ("device" in r.error.message or "network" in r.error.message), (mod, r)
