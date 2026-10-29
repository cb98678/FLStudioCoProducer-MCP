from coproducer.services import set_service


def test_accepts_a_sandbox_project(rig, desk, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    (tmp_path / "p").mkdir()
    (tmp_path / "p" / "song.flp").write_bytes(b"FLhd")
    desk.fake.main["title"] = "song.flp - FL Studio 2026"
    r = rig.call("check_sandbox_project_open")
    assert r.ok and r.value["project"] == "song.flp"
    desk.fake.main["title"] = "song.flp* - FL Studio 2026"
    assert rig.call("check_sandbox_project_open").ok


def test_refuses_unsaved_and_foreign_projects(rig, desk, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    desk.fake.main["title"] = "FL Studio 2026"
    assert rig.call("check_sandbox_project_open").error.code == "E_SANDBOX_VIOLATION"
    desk.fake.main["title"] = "mine.flp - FL Studio 2026"
    assert rig.call("check_sandbox_project_open").error.code == "E_SANDBOX_VIOLATION"
    (tmp_path / "Backup").mkdir()
    (tmp_path / "Backup" / "mine.flp").write_bytes(b"FLhd")           # a backup copy does not count
    assert rig.call("check_sandbox_project_open").error.code == "E_SANDBOX_VIOLATION"
