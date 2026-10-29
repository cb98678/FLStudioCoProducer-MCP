import json

from coproducer.services import set_service

EM, EN = chr(0x2014), chr(0x2013)


def test_writes_json_and_markdown(rig, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    r = rig.call("write_report_file", path=str(tmp_path / "r.json"), content={"lufs": -14.2, "note": "a " + EM + " b"})
    assert r.ok and json.loads((tmp_path / "r.json").read_text()) == {"lufs": -14.2, "note": "a - b"}
    m = rig.call("write_report_file", path=str(tmp_path / "r.md"), content="# Mix\nlevel " + EN + " fine", fmt="markdown")
    text = (tmp_path / "r.md").read_text()
    assert m.ok and text == "# Mix\nlevel - fine\n" and m.value["bytes"] == len(text)


def test_sandbox_and_format_errors(rig, tmp_path):
    assert rig.call("write_report_file", path=str(tmp_path / "a.json"), content={}).error.code == "E_SANDBOX_VIOLATION"
    set_service("sandbox_root", str(tmp_path / "box"))
    (tmp_path / "box").mkdir()
    assert rig.call("write_report_file", path=str(tmp_path / "x.json"), content={}).error.code == "E_SANDBOX_VIOLATION"
    ok_path = str(tmp_path / "box" / "a.json")
    assert rig.call("write_report_file", path=ok_path, content="text").error.code == "E_ARG"
    assert rig.call("write_report_file", path=ok_path, content={"a": 1}, fmt="markdown").error.code == "E_ARG"
    assert rig.call("write_report_file", path=str(tmp_path / "box" / "no" / "dir.json"), content={}).error.code == "E_IO"
