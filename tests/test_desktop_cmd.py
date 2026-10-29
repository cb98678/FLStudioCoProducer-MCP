"""coproducer install-desktop: where the config lives, merge without losing other servers, backup, dry run, remove, bad JSON."""
import json
import sys
from pathlib import Path

import pytest

from coproducer.cli import build_parser, commands, desktop_cmd as D


def test_config_path_per_platform(tmp_path):
    assert str(D.config_path({"APPDATA": "C:\\Users\\m\\AppData\\Roaming", "LOCALAPPDATA": str(tmp_path / "nolocal")}, "win32", tmp_path)).replace("\\", "/").endswith("AppData/Roaming/Claude/claude_desktop_config.json")
    assert D.config_path({}, "win32", tmp_path) == tmp_path / "AppData/Roaming/Claude/claude_desktop_config.json"
    assert D.config_path({}, "darwin", tmp_path) == tmp_path / "Library/Application Support/Claude/claude_desktop_config.json"
    assert D.config_path({"XDG_CONFIG_HOME": str(tmp_path / "x")}, "linux", tmp_path) == tmp_path / "x/Claude/claude_desktop_config.json"


def test_entries_use_absolute_paths_and_the_given_python(tmp_path):
    e = D.build_entries(tmp_path, python="C:/py/python.exe")
    assert sorted(e) == ["coproducer-fl-bridge", "coproducer-studio-audio", "coproducer-studio-ml"]
    a = e["coproducer-fl-bridge"]
    assert a["command"] == "C:/py/python.exe" and a["args"][:4] == ["-m", "coproducer", "--home", str(tmp_path.resolve())]
    assert a["args"][4:] == ["serve", "fl-bridge", "--run", "default"]
    dc = D.build_entries(tmp_path, servers=("desktop-control",), ceiling="A1")["coproducer-desktop-control"]
    assert dc["args"][-2:] == ["--ceiling", "A1"]
    with pytest.raises(ValueError):
        D.build_entries(tmp_path, servers=("nope",))


def test_install_keeps_other_servers_and_keys_and_backs_up(tmp_path):
    cfg = tmp_path / "Claude" / "claude_desktop_config.json"
    cfg.parent.mkdir()
    cfg.write_text(json.dumps({"theme": "x", "mcpServers": {"other": {"command": "node", "args": ["a.js"]}}}))
    r = D.install(tmp_path, config=cfg, python="py")
    data = json.loads(cfg.read_text())
    assert data["theme"] == "x" and data["mcpServers"]["other"] == {"command": "node", "args": ["a.js"]}
    assert set(data["mcpServers"]) == {"other", *D.build_entries(tmp_path, python="py")}
    assert r["changed"] and r["others_kept"] == ["other"] and Path(r["backup"]).is_file()
    assert json.loads(Path(r["backup"]).read_text())["mcpServers"] == {"other": {"command": "node", "args": ["a.js"]}}
    again = D.install(tmp_path, config=cfg, python="py")          # idempotent: no change, no new backup
    assert not again["changed"] and again["backup"] is None and again["result"]["unchanged"]
    assert "Nothing to change" in D.render(again)


def test_dry_run_writes_nothing_and_new_file_is_created(tmp_path):
    cfg = tmp_path / "new" / "claude_desktop_config.json"
    r = D.install(tmp_path, config=cfg, dry_run=True)
    assert r["changed"] and not cfg.exists() and "DRY RUN" in D.render(r)
    r = D.install(tmp_path, config=cfg)
    assert cfg.is_file() and r["backup"] is None and "fully quit Claude Desktop" in D.render(r)


def test_update_when_home_changes(tmp_path):
    cfg = tmp_path / "c.json"
    D.install(tmp_path / "a", config=cfg, python="py")
    r = D.install(tmp_path / "b", config=cfg, python="py")
    assert len(r["result"]["updated"]) == 3


def test_remove_only_touches_coproducer_entries(tmp_path):
    cfg = tmp_path / "c.json"
    cfg.write_text(json.dumps({"mcpServers": {"other": {"command": "x"}}}))
    D.install(tmp_path, config=cfg)
    r = D.install(tmp_path, config=cfg, remove=True)
    assert sorted(r["result"]["removed"]) == sorted(D.build_entries(tmp_path)) and json.loads(cfg.read_text())["mcpServers"] == {"other": {"command": "x"}}


@pytest.mark.parametrize("text", ["{not json", "[1]", '{"mcpServers": []}'])
def test_bad_config_is_refused_and_left_alone(tmp_path, text):
    cfg = tmp_path / "c.json"
    cfg.write_text(text)
    with pytest.raises(ValueError):
        D.install(tmp_path, config=cfg)
    assert cfg.read_text() == text and not list(tmp_path.glob("*.bak"))


def test_utf8_bom_is_accepted(tmp_path):
    cfg = tmp_path / "c.json"
    cfg.write_bytes(b"\xef\xbb\xbf" + json.dumps({"mcpServers": {}}).encode())
    assert D.install(tmp_path, config=cfg)["changed"]


def test_cli_wiring(tmp_path, capsys):
    p = build_parser()
    a = p.parse_args(["--home", str(tmp_path), "install-desktop", "--config", str(tmp_path / "c.json"), "--with-desktop-control", "--dry-run"])
    lines = []
    assert commands.cmd_install_desktop(tmp_path, a, lines.append) == 0 and "DRY RUN" in lines[0]
    a = p.parse_args(["--home", str(tmp_path), "install-desktop", "--config", str(tmp_path / "c.json"), "--with-desktop-control"])
    assert commands.cmd_install_desktop(tmp_path, a, lines.append) == 0
    assert "coproducer-desktop-control" in json.loads((tmp_path / "c.json").read_text())["mcpServers"]
    (tmp_path / "bad.json").write_text("{")
    a = p.parse_args(["install-desktop", "--config", str(tmp_path / "bad.json")])
    assert commands.cmd_install_desktop(tmp_path, a, lines.append) == 1
    assert p.parse_args(["setup", "--desktop"]).desktop and p.parse_args(["setup", "--no-desktop"]).no_desktop


def test_setup_prompt_yes_no_and_non_interactive(tmp_path, monkeypatch):
    cfg = tmp_path / "c.json"
    monkeypatch.setattr(D, "config_path", lambda *a, **k: cfg)
    out = []
    assert D.ask_and_install(tmp_path, ask=lambda _: "n", out=out.append) is None and not cfg.exists()
    assert D.ask_and_install(tmp_path, ask=lambda _: "y", out=out.append)["changed"] and cfg.is_file()
    monkeypatch.setattr(sys, "stdin", open("/dev/null") if sys.platform != "win32" else sys.stdin)
    assert D.ask_and_install(tmp_path, out=out.append) is None      # stdin is not a terminal: never prompts


def test_no_em_dash_in_output(tmp_path):
    r = D.install(tmp_path, config=tmp_path / "c.json", dry_run=True)
    assert "\u2014" not in D.render(r) and "\u2014" not in Path(D.__file__).read_text(encoding="utf-8")


def _serum_home(tmp_path):
    clone = tmp_path / "sandbox" / "third_party" / "serum-mcp"
    (clone / ".venv").mkdir(parents=True)
    (clone / "pyproject.toml").write_text("[project]\nname='serum-mcp'\n")
    user = tmp_path / "user"
    root = user / "Documents" / "Xfer" / "Serum 2 Presets"
    for sub in ("Presets/User", "Presets/Factory", "Tables", "Samples"):
        (root / sub).mkdir(parents=True)
    uv = tmp_path / "uv.exe"
    uv.write_text("")
    return clone, user, root, uv


def test_serum_mcp_is_registered_from_its_clone_with_the_serum_folders(tmp_path):
    clone, user, root, uv = _serum_home(tmp_path)
    e = D.serum_entry(tmp_path, uv=str(uv), user_home=user)["coproducer-serum"]
    assert e["command"] == str(uv.resolve()) and e["args"] == ["run", "--frozen", "--directory", str(clone.resolve()), "serum-mcp"]
    assert e["env"] == {"SERUM_PRESETS_PATH": str(root / "Presets" / "User"), "SERUM_TABLES_PATH": str(root / "Tables"),
                        "SERUM_SAMPLES_PATH": str(root / "Samples")}
    r = D.install(tmp_path, config=tmp_path / "c.json", serum={"uv": str(uv), "presets": root / "Presets" / "User"}, claude_code=True)
    servers = json.loads((tmp_path / "c.json").read_text())["mcpServers"]
    assert "coproducer-serum" in servers and "coproducer-fl-bridge" in servers
    cc = json.loads((tmp_path / ".mcp.json").read_text())["mcpServers"]
    assert cc["coproducer-serum"]["type"] == "stdio" and set(cc) == set(servers) and "Claude Code" in D.render(r)
    assert "coproducer-serum" in D.install(tmp_path, config=tmp_path / "c.json", remove=True)["result"]["removed"]


def test_serum_mcp_refuses_what_is_missing(tmp_path):
    with pytest.raises(ValueError, match="not cloned"):
        D.serum_entry(tmp_path, uv="uv", user_home=tmp_path)
    clone, user, root, uv = _serum_home(tmp_path)
    with pytest.raises(ValueError, match="Serum 2 user preset folder"):
        D.serum_entry(tmp_path, uv=str(uv), user_home=tmp_path / "nobody")
    (clone / ".venv").rmdir()
    with pytest.raises(ValueError, match="uv sync"):
        D.serum_entry(tmp_path, uv=str(uv), user_home=user)


def test_the_store_build_reads_its_own_packaged_config(tmp_path):
    """rtxclub, 2026-10-26: Claude Desktop from the Microsoft Store reads LocalCache inside its package; the plain AppData file is ignored."""
    env = {"APPDATA": str(tmp_path / "Roaming"), "LOCALAPPDATA": str(tmp_path / "Local")}
    plain = tmp_path / "Roaming" / "Claude"
    plain.mkdir(parents=True)
    assert D.config_path(env, "win32") == plain / "claude_desktop_config.json"            # the .exe build: no package folder
    pkg = tmp_path / "Local" / "Packages" / "Claude_pzs8sxrjxfjjc" / "LocalCache" / "Roaming" / "Claude"
    pkg.parents[2].mkdir(parents=True)                                     # installed, never started: no LocalCache yet
    assert D.config_path(env, "win32") == pkg / "claude_desktop_config.json"
    pkg.mkdir(parents=True)
    assert D.config_path(env, "win32") == pkg / "claude_desktop_config.json"
    (plain / "claude_desktop_config.json").write_text(json.dumps({"mcpServers": {"coproducer-fl-bridge": {"command": "x"}, "other": {"command": "y"}}}))
    assert D.unused_config_paths(env, "win32") == [plain / "claude_desktop_config.json"]
    assert D.unused_config_paths(env, "darwin", tmp_path) == []


def test_install_cleans_entries_from_the_file_desktop_does_not_read(tmp_path, monkeypatch):
    used, unused = tmp_path / "used.json", tmp_path / "unused.json"
    unused.write_text(json.dumps({"mcpServers": {"coproducer-fl-bridge": {"command": "old"}, "fl-studio": {"command": "uv"}}}))
    monkeypatch.setattr(D, "config_path", lambda *a, **k: used)
    monkeypatch.setattr(D, "unused_config_paths", lambda *a, **k: [unused])
    r = D.install(tmp_path)
    assert r["stale"] == [{"file": str(unused), "removed": ["coproducer-fl-bridge"]}] and "does not read" in D.render(r)
    assert json.loads(unused.read_text())["mcpServers"] == {"fl-studio": {"command": "uv"}}            # other servers stay
    assert "coproducer-fl-bridge" in json.loads(used.read_text())["mcpServers"]


def test_desktop_is_told_apart_from_claude_code():
    assert D.is_desktop_exe(r"C:\Program Files\WindowsApps\Claude_3.6556.2.0_x64__pzs8sxrjxfjjc\app\Claude.exe")
    assert D.is_desktop_exe(r"C:\Users\m\AppData\Local\AnthropicClaude\app-2.4\claude.exe")
    assert not D.is_desktop_exe(r"C:\Users\m\.local\bin\claude.exe") and not D.is_desktop_exe("")


def test_never_written_while_desktop_runs_unless_asked(tmp_path, monkeypatch):
    """rtxclub 2026-10-26: Desktop rewrote the file from memory on a setting change and the entries added while it ran were gone."""
    cfg = tmp_path / "c.json"
    monkeypatch.setattr(D, "config_path", lambda *a, **k: cfg)
    monkeypatch.setattr(D, "unused_config_paths", lambda *a, **k: [])
    running = [["C:/Program Files/WindowsApps/Claude_x/app/Claude.exe"]]
    monkeypatch.setattr(D, "desktop_processes", lambda *a, **k: running[0])
    p, lines = build_parser(), []
    assert commands.cmd_install_desktop(tmp_path, p.parse_args(["install-desktop"]), lines.append) == 2
    assert not cfg.exists() and "running" in lines[-1]
    monkeypatch.setattr(D, "wait_for_quit", lambda minutes, out: False)
    assert commands.cmd_install_desktop(tmp_path, p.parse_args(["install-desktop", "--wait"]), lines.append) == 3 and not cfg.exists()

    def quit_now(minutes, out):
        running[0] = []
        return True
    monkeypatch.setattr(D, "wait_for_quit", quit_now)
    monkeypatch.setattr(D, "desktop_start_times", lambda *a, **k: [])
    started = []
    monkeypatch.setattr(D, "start_desktop", lambda: started.append(1) or "Claude_x!Claude")
    assert commands.cmd_install_desktop(tmp_path, p.parse_args(["install-desktop", "--wait", "--restart"]), lines.append) == 0
    assert "coproducer-fl-bridge" in json.loads(cfg.read_text())["mcpServers"] and started == [1]
    assert "Claude Desktop is closed" in lines[-2] and "Started Claude Desktop again" in lines[-1]


def test_wait_for_quit_polls_until_desktop_is_gone():
    seen = iter([["x"], ["x"], ["x"], []])
    msgs = []
    assert D.wait_for_quit(1, msgs.append, procs=lambda: next(seen), sleep=lambda s: None) and "Quit Claude Desktop now" in msgs[0]
    assert D.wait_for_quit(1, msgs.append, procs=lambda: [], sleep=lambda s: None)
    assert not D.wait_for_quit(0.0001, msgs.append, procs=lambda: ["x"], sleep=lambda s: None)


def test_a_desktop_reopened_before_the_write_is_waited_out_again(tmp_path, monkeypatch):
    """rtxclub 2026-10-27: the person reopened Claude Desktop 3 s after quitting; it read the old file one second before the write."""
    cfg = tmp_path / "c.json"
    monkeypatch.setattr(D, "config_path", lambda *a, **k: cfg)
    monkeypatch.setattr(D, "unused_config_paths", lambda *a, **k: [])
    state = {"procs": ["C:/Program Files/WindowsApps/Claude_x/app/Claude.exe"], "starts": [[1.0], []], "waits": 0}
    monkeypatch.setattr(D, "desktop_processes", lambda *a, **k: state["procs"])
    monkeypatch.setattr(D, "desktop_start_times", lambda *a, **k: state["starts"].pop(0))

    def wait(minutes, out):
        state["waits"] += 1
        return True
    monkeypatch.setattr(D, "wait_for_quit", wait)
    monkeypatch.setattr(D, "start_desktop", lambda: "x")
    lines = []
    assert commands.cmd_install_desktop(tmp_path, build_parser().parse_args(["install-desktop", "--wait"]), lines.append) == 0
    assert state["waits"] == 2 and any("opened again before" in x for x in lines) and "has loaded the servers" in lines[-1]
    state["starts"] = [[1.0]]
    assert commands.cmd_install_desktop(tmp_path, build_parser().parse_args(["install-desktop", "--force"]), lines.append) == 0
    monkeypatch.setattr(D, "desktop_processes", lambda *a, **k: [])
    state["starts"] = [[1.0]]
    assert commands.cmd_install_desktop(tmp_path, build_parser().parse_args(["install-desktop"]), lines.append) == 4


def test_process_list_parsing_keeps_only_desktop(monkeypatch):
    class P:
        stdout = ("C:\\Program Files\\WindowsApps\\Claude_3.6_x64__pz\\app\\Claude.exe|1793113743000\n"
                  "C:\\Users\\m\\.local\\bin\\claude.exe|1793113743000\nC:\\Program Files\\WindowsApps\\Claude_3.6_x64__pz\\app\\Claude.exe|\n")
    monkeypatch.setattr(D.sys, "platform", "win32")
    assert D._desktop_procs(lambda *a, **k: P()) == [("C:\\Program Files\\WindowsApps\\Claude_3.6_x64__pz\\app\\Claude.exe", 1793113743.0),
                                                    ("C:\\Program Files\\WindowsApps\\Claude_3.6_x64__pz\\app\\Claude.exe", None)]


def test_check_servers_fails_a_server_with_no_tools(tmp_path, monkeypatch):
    from coproducer.cli import servers_check as SC
    cfg = tmp_path / "c.json"
    cfg.write_text(json.dumps({"mcpServers": {"coproducer-studio-ml": {"command": "x", "args": []}, "coproducer-fl-bridge": {"command": "y", "args": []},
                                              "other": {"command": "z"}}}))

    async def fake(entry):
        return {"tools": 0 if entry["command"] == "x" else 27, "skills": None, "sample": []}
    monkeypatch.setattr(SC, "_one", fake)
    rows = {r["name"]: r for r in SC.check(cfg)}
    assert set(rows) == {"coproducer-studio-ml", "coproducer-fl-bridge"}
    assert not rows["coproducer-studio-ml"]["ok"] and rows["coproducer-fl-bridge"]["ok"]
    assert "FAIL  coproducer-studio-ml" in SC.render(list(rows.values()), cfg) and "lists no tools" in SC.render(list(rows.values()), cfg)
