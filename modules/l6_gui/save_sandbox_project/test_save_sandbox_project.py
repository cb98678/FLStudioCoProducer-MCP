import os


def _project(tmp_path):
    f = tmp_path / "probe_scratch.flp"
    f.write_bytes(b"FLhd")
    os.utime(f, (1, 1))
    return f


def test_saves_when_the_title_names_the_file(rig, desk, tmp_path):
    f = _project(tmp_path)
    desk.fake.main["title"] = "probe_scratch - FL Studio 2026"
    desk.fake.reactions.append(lambda fake, ev: f.write_bytes(b"FLhd-saved") if ev == ("hotkey", ("ctrl", "s")) else None)
    r = rig.call("save_sandbox_project", project=str(f), wait_s=2)
    assert r.ok and r.meta["verified"] is True and r.value["bytes"] == 10


def test_refusals(rig, desk, tmp_path):
    f = _project(tmp_path)
    assert rig.call("save_sandbox_project", project="/elsewhere/p.flp").error.code == "E_SANDBOX_VIOLATION"
    assert rig.call("save_sandbox_project", project=str(tmp_path / "gone.flp")).error.code == "E_NOT_FOUND"
    wrong = rig.call("save_sandbox_project", project=str(f), wait_s=1)           # the fake window is titled "FL Studio 2026"
    assert wrong.error.code == "E_GUI_MISMATCH" and "FL Studio 2026" in wrong.error.message and not desk.fake.log[1:]
    desk.fake.main["title"] = "probe_scratch - FL Studio 2026"
    assert rig.call("save_sandbox_project", project=str(f), wait_s=1).error.code == "E_NOT_VERIFIED"
