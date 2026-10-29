from pathlib import Path

from coproducer.config import render_config, load_config
from coproducer.services import clear_services, get_service
from coproducer.wiring import FileHalt, install_services


def test_install_services_from_config(tmp_path):
    home = tmp_path / "home"
    (home / "models").mkdir(parents=True)
    (home / "models" / "registry.toml").write_text((Path(__file__).resolve().parents[1] / "models" / "registry.toml").read_text())
    cfg = load_config(home)
    cfg["fl"]["exe"] = "C:/fl/FL64.exe"
    cfg["desktop"]["allow_unverified"] = True
    cfg["anchors"] = {"export_start": "120,340", "broken": "x"}
    (home / "config.toml").write_text(render_config(cfg))
    try:
        install_services(home, tmp_path / "run")
        assert get_service("fl_exe") == "C:/fl/FL64.exe"
        assert get_service("desktop_config")["anchors"] == {"export_start": [120, 340]}
        assert get_service("desktop_config")["allow_unverified"] is True
        assert get_service("scheduler") is not None and "demucs" in get_service("scheduler").registry
        assert Path(get_service("recipes_dir")).name == "gui_recipes"
        assert (home / "sandbox").is_dir()
    finally:
        clear_services()


def test_file_halt_is_shared_between_processes(tmp_path):
    a, b = FileHalt(tmp_path / "run"), FileHalt(tmp_path / "run")
    assert not b.is_set()
    a.set()
    assert b.is_set()


def test_blank_fl_settings_fall_back_to_detected_paths(tmp_path, monkeypatch):
    from coproducer.cli import detect

    home = tmp_path / "home"
    (home / "models").mkdir(parents=True)
    (home / "models" / "registry.toml").write_text((Path(__file__).resolve().parents[1] / "models" / "registry.toml").read_text())
    pf = tmp_path / "pf"
    for ver in ("FL Studio 20", "FL Studio 21", "FL Studio 21BETA", "FL Studio 2024", "FL Studio 2026"):
        (pf / "Image-Line" / ver).mkdir(parents=True)
        (pf / "Image-Line" / ver / "FL64.exe").write_text("")
    monkeypatch.setattr(detect, "fl_exe_candidates", lambda env=None: sorted((pf / "Image-Line").glob("FL Studio*/FL64.exe")))
    monkeypatch.setattr(detect, "fl_data_dir", lambda home=None: tmp_path / "docs" / "FL Studio")
    try:
        install_services(home, tmp_path / "run")
        assert get_service("fl_exe").endswith("FL Studio 2026/FL64.exe") or get_service("fl_exe").endswith("FL Studio 2026\\FL64.exe")
        assert Path(get_service("piano_roll_scripts_dir")) == tmp_path / "docs" / "FL Studio" / "Settings" / "Piano roll scripts"
    finally:
        clear_services()


def test_setup_and_doctor_pick_the_newest_release_not_the_last_name(tmp_path, monkeypatch):
    """'FL Studio 21BETA' sorts after 'FL Studio 2026' by name; setup wrote the old beta into config.toml on a real machine."""
    from coproducer.cli import detect, doctor, setup_cmd

    pf = tmp_path / "pf" / "Image-Line"
    names = ("FL Studio 20", "FL Studio 21", "FL Studio 21BETA", "FL Studio 2024", "FL Studio 2026")
    for ver in names:
        (pf / ver).mkdir(parents=True)
        (pf / ver / "FL64.exe").write_text("")
    monkeypatch.setattr(detect, "fl_exe_candidates", lambda env=None: sorted(pf.glob("FL Studio*/FL64.exe")))
    assert detect.newest_fl_exe().parent.name == "FL Studio 2026"
    home = tmp_path / "home"
    home.mkdir()
    (home / "models").mkdir()
    rep = setup_cmd.run_setup(home, data_dir=str(tmp_path / "data"))
    assert "FL Studio 2026" in rep["fl_exe"], rep
    row = doctor.check_fl({"fl": {"exe": ""}})
    assert row["status"] == "warn" and "FL Studio 2026" in row["fix"], row
