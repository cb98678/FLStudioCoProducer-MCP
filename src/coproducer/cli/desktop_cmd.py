"""coproducer install-desktop: register the MCP servers with Claude Desktop (claude_desktop_config.json).

Merges into the existing "mcpServers" object and keeps every other server and key. Entries use absolute paths
(Claude Desktop starts them from its own working directory) and the Python that is running this command, so no PATH setup is needed.
Format and location: https://modelcontextprotocol.io/docs/develop/connect-local-servers
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

PREFIX = "coproducer-"
DEFAULT_SERVERS = ("fl-bridge", "studio-audio", "studio-ml")
ALL_SERVERS = DEFAULT_SERVERS + ("desktop-control",)
SERUM_NAME = PREFIX + "serum"
SERUM_CLONE = Path("sandbox") / "third_party" / "serum-mcp"
# Serum 2's own default user preset folder (the serum-mcp server derives Factory, Tables and Samples from it: keep it at Presets\User).
SERUM_PRESETS = Path("Documents") / "Xfer" / "Serum 2 Presets" / "Presets" / "User"


def _win_dirs(env: dict, home: Path) -> tuple[list[Path], Path]:
    """(MSIX package folders Claude Desktop reads from, the plain %APPDATA%\\Claude folder)."""
    local = Path(env["LOCALAPPDATA"]) if env.get("LOCALAPPDATA") else home / "AppData" / "Local"
    roaming = Path(env["APPDATA"]) if env.get("APPDATA") else home / "AppData" / "Roaming"
    # The package folder exists from the moment the Store build is installed; LocalCache\Roaming\Claude only after its first start. The
    # installer may register the servers before that first start, so the file goes where the packaged app will read it either way.
    return sorted(p / "LocalCache" / "Roaming" / "Claude" for p in local.glob("Packages/Claude_*") if p.is_dir()), roaming / "Claude"


def config_path(env: dict | None = None, platform: str | None = None, home: Path | None = None) -> Path:
    """The config file Claude Desktop actually reads. Windows: the Microsoft Store, WinGet or MSIX build keeps it inside its package,
    %LOCALAPPDATA%\\Packages\\Claude_<id>\\LocalCache\\Roaming\\Claude (Windows redirects the app's AppData there, so the plain
    %APPDATA%\\Claude file is never read by it: found on rtxclub 2026-10-26, where three days of entries there never loaded); the .exe
    installer build uses %APPDATA%\\Claude. macOS: ~/Library/Application Support/Claude. Linux: ~/.config/Claude.
    Sources: https://exchangepedia.com/2026/04/claudetools-claude-desktop-powershell-module.html and
    https://modelcontextprotocol.io/docs/develop/connect-local-servers"""
    env = os.environ if env is None else env
    platform = sys.platform if platform is None else platform
    home = Path.home() if home is None else home
    if platform.startswith("win"):
        packaged, plain = _win_dirs(env, home)
        return (packaged[0] if packaged else plain) / "claude_desktop_config.json"
    if platform == "darwin":
        base = home / "Library" / "Application Support"
    else:
        base = Path(env["XDG_CONFIG_HOME"]) if env.get("XDG_CONFIG_HOME") else home / ".config"
    return base / "Claude" / "claude_desktop_config.json"


def unused_config_paths(env: dict | None = None, platform: str | None = None, home: Path | None = None) -> list[Path]:
    """Config files Claude Desktop does not read on this machine (Windows with the MSIX build: the plain %APPDATA% one). Old coproducer
    entries there only mislead, so install and remove take them out."""
    env = os.environ if env is None else env
    platform = sys.platform if platform is None else platform
    home = Path.home() if home is None else home
    if not platform.startswith("win"):
        return []
    packaged, plain = _win_dirs(env, home)
    used = config_path(env, platform, home)
    return [p / "claude_desktop_config.json" for p in packaged[1:] + [plain] if (p / "claude_desktop_config.json") != used and (p / "claude_desktop_config.json").is_file()]


def log_dir(cfg: Path, env: dict | None = None) -> Path:
    """Where Claude Desktop writes mcp.log and mcp-server-NAME.log: %LOCALAPPDATA%\\Claude\\logs on Windows when it exists (the Store
    build writes there, rtxclub 2026-10-26), else next to the config."""
    env = os.environ if env is None else env
    if env.get("LOCALAPPDATA") and (Path(env["LOCALAPPDATA"]) / "Claude" / "logs").is_dir():
        return Path(env["LOCALAPPDATA"]) / "Claude" / "logs"
    return cfg.parent / "logs"


# Claude Desktop keeps claude_desktop_config.json in memory (its own preferences live in the same file) and writes the whole file back
# whenever one of its settings changes. On rtxclub (2026-10-26) entries added while it ran were gone after two such writes (a folder grant
# at 23:08 and 03:44), so it never started them. The file is only written while Desktop is closed.
RUNNING_HELP = ("Claude Desktop is running. It keeps this file in memory and writes it back whenever one of its settings changes, which "
                "removes servers added while it runs. Quit it (right-click its icon by the clock, then Quit) and run this again, or run  "
                "coproducer install-desktop --wait --restart  and quit it when asked.")


def is_desktop_exe(path: str) -> bool:
    """A Claude Desktop executable (the Microsoft Store package or the installer build), not Claude Code's own claude.exe."""
    low = (path or "").lower().replace("/", "\\")
    return "\\windowsapps\\claude_" in low or "\\anthropicclaude\\" in low


def _desktop_procs(run=subprocess.run) -> list:
    """[(executable path, start time in Unix seconds or None)] of the running Claude Desktop processes; empty on other systems."""
    if sys.platform != "win32":
        return []
    cmd = ("Get-Process -Name claude -ErrorAction SilentlyContinue | ForEach-Object { $t = ''; "
           "try { $t = ([DateTimeOffset]$_.StartTime).ToUnixTimeMilliseconds() } catch { }; $_.Path + '|' + $t }")
    try:
        p = run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return []
    out = []
    for line in (p.stdout or "").splitlines():
        path, _, t = line.strip().rpartition("|")
        if is_desktop_exe(path):
            out.append((path, int(t) / 1000.0 if t.isdigit() else None))
    return out


def desktop_processes(run=subprocess.run) -> list:
    """Executable paths of the running Claude Desktop processes. Empty on other systems, or when it is not running."""
    return [p for p, _ in _desktop_procs(run)]


def desktop_start_times(run=subprocess.run) -> list:
    """Start times (Unix seconds) of the running Claude Desktop processes."""
    return [t for _, t in _desktop_procs(run) if t is not None]


def wait_for_quit(minutes: float, out=print, procs=desktop_processes, sleep=time.sleep, poll_s: float = 0.5) -> bool:
    """Wait until Claude Desktop is no longer running. True when it is closed, False when the time ran out. It polls often, because the
    file has to be written in the moment between Desktop closing and anyone opening it again (rtxclub 2026-10-27: reopened 3 s after
    quitting, it read the old file one second before the write)."""
    if not procs():
        return True
    out("Quit Claude Desktop now: right-click its icon by the clock, then Quit (closing the window is not enough), and leave it closed:"
        " it is opened again for you. Waiting up to %d minutes..." % round(minutes))
    end = time.monotonic() + minutes * 60
    while time.monotonic() < end:
        sleep(poll_s)
        if not procs():
            return True
    return False


def start_desktop(run=subprocess.run, popen=subprocess.Popen) -> str | None:
    """Start Claude Desktop (the Store package through its app id, else the installer build). Returns what was started, or None."""
    if sys.platform != "win32":
        return None
    try:
        p = run(["powershell", "-NoProfile", "-Command", "Get-StartApps | Where-Object { $_.Name -eq 'Claude' } | ForEach-Object { $_.AppID }"],
                capture_output=True, text=True, timeout=60)
        ids = [x.strip() for x in (p.stdout or "").splitlines() if x.strip()]
    except (OSError, subprocess.TimeoutExpired):
        ids = []
    ids.sort(key=lambda x: "!" not in x)                      # the packaged app id (Family!App) first
    if ids:
        popen(["explorer.exe", "shell:AppsFolder\\" + ids[0]])
        return ids[0]
    exe = Path(os.environ.get("LOCALAPPDATA", "")) / "AnthropicClaude" / "claude.exe"
    if exe.is_file():
        popen([str(exe)])
        return str(exe)
    return None


def build_entries(home: Path, *, python: str | None = None, servers=DEFAULT_SERVERS, run_id: str = "default", ceiling: str = "A2") -> dict:
    """{'coproducer-fl-bridge': {'command': <python>, 'args': ['-m','coproducer','--home',<abs>,'serve','fl-bridge','--run',<id>]}, ...}"""
    py = python or sys.executable
    out = {}
    for s in servers:
        if s not in ALL_SERVERS:
            raise ValueError("unknown server: " + s)
        args = ["-m", "coproducer", "--home", str(Path(home).resolve()), "serve", s, "--run", run_id]
        if s == "desktop-control":
            args += ["--ceiling", ceiling]
        out[PREFIX + s] = {"command": py, "args": args}
    return out


def serum_entry(home: Path, *, uv: str | None = None, presets: Path | None = None, sample_bank: Path | None = None,
                user_home: Path | None = None) -> dict:
    """The third-party serum-mcp server (https://github.com/Celian-mrc/serum-mcp) run from its clone with its locked packages.

    Its tools write .SerumPreset files under SERUM_PRESETS_PATH; the co-producer's rule is a subfolder named sandbox (generate_preset
    subfolder "sandbox/<song>"), so nothing of the person's own library is touched. Raises ValueError naming what is missing.
    """
    clone = (Path(home) / SERUM_CLONE).resolve()
    if not (clone / "pyproject.toml").is_file():
        raise ValueError("serum-mcp is not cloned at %s (see docs/SERUM_MCP.md)" % clone)
    if not (clone / ".venv").is_dir():
        raise ValueError("serum-mcp has no environment yet: run  uv sync --frozen  inside %s" % clone)
    uv = uv or shutil.which("uv")
    if not uv:
        raise ValueError("uv was not found on PATH; install uv or pass --uv C:\\path\\to\\uv.exe")
    if not presets:
        from .detect import documents_dir
        presets = (user_home / SERUM_PRESETS) if user_home else documents_dir() / SERUM_PRESETS.relative_to("Documents")
    presets = Path(presets)
    if not presets.is_dir():
        raise ValueError("no Serum 2 user preset folder at %s; pass --serum-presets (Serum menu: Show Serum Presets folder, then Presets\\User)" % presets)
    env = {"SERUM_PRESETS_PATH": str(presets)}
    for key, sub in (("SERUM_TABLES_PATH", "Tables"), ("SERUM_SAMPLES_PATH", "Samples")):
        if (presets.parent.parent / sub).is_dir():
            env[key] = str(presets.parent.parent / sub)
    if sample_bank:
        env["SAMPLE_BANK_PATH"] = str(Path(sample_bank))
    if (Path(home) / "runtime" / "python").is_dir():          # install.ps1 keeps uv's Pythons there; the clone's .venv was made from one of them
        env["UV_PYTHON_INSTALL_DIR"] = str((Path(home) / "runtime" / "python").resolve())
    return {SERUM_NAME: {"command": str(Path(uv).resolve()) if Path(uv).exists() else uv,
                         "args": ["run", "--frozen", "--directory", str(clone), "serum-mcp"], "env": env}}


def claude_code_file(home: Path, entries: dict, dry_run: bool = False) -> dict:
    """Write the same servers to <home>/.mcp.json, the project-scoped file Claude Code reads (it asks once before using them).
    Format: https://code.claude.com/docs/en/mcp . Keeps other servers in the file."""
    path = Path(home).resolve() / ".mcp.json"
    data = load_config_file(path)
    new, res = merge(data, {k: {"type": "stdio", **v} for k, v in entries.items()})
    changed = new != data
    if changed and not dry_run:
        write_atomic(path, new)
    return {"file": str(path), "changed": changed, "result": res}


def load_config_file(path: Path) -> dict:
    """Existing config as a dict. Missing or empty file is {}. Raises ValueError for anything that is not a JSON object."""
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8-sig")
    if not text.strip():
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError("%s is not valid JSON (%s); fix or move it, nothing was changed" % (path, e)) from e
    if not isinstance(data, dict):
        raise ValueError("%s must hold a JSON object" % path)
    if "mcpServers" in data and not isinstance(data["mcpServers"], dict):
        raise ValueError("%s: mcpServers must be an object" % path)
    return data


def merge(data: dict, entries: dict) -> tuple[dict, dict]:
    """Returns (new config, {'added': [...], 'updated': [...], 'unchanged': [...]}). Does not touch the input."""
    new = json.loads(json.dumps(data))
    cur = new.setdefault("mcpServers", {})
    res = {"added": [], "updated": [], "unchanged": []}
    for k, v in entries.items():
        if k not in cur:
            res["added"].append(k)
        elif cur[k] == v:
            res["unchanged"].append(k)
        else:
            res["updated"].append(k)
        cur[k] = v
    return new, res


def strip(data: dict) -> tuple[dict, list]:
    """Remove every coproducer-* entry. Returns (new config, removed names)."""
    new = json.loads(json.dumps(data))
    cur = new.get("mcpServers", {})
    gone = [k for k in cur if k.startswith(PREFIX)]
    for k in gone:
        del cur[k]
    return new, gone


def write_atomic(path: Path, data: dict) -> Path | None:
    """Back up an existing file (config.json.coproducer-YYYYmmdd-HHMMSS.bak), then write through a temp file. Returns the backup path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    bak = None
    if path.is_file():
        bak = path.with_name(path.name + ".coproducer-" + time.strftime("%Y%m%d-%H%M%S") + ".bak")
        shutil.copyfile(path, bak)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, path)
    return bak


def install(home: Path, *, config: Path | None = None, servers=DEFAULT_SERVERS, run_id: str = "default", ceiling: str = "A2",
            python: str | None = None, dry_run: bool = False, remove: bool = False, serum: dict | None = None,
            claude_code: bool = False) -> dict:
    """serum: keyword arguments for serum_entry (None leaves serum-mcp out). claude_code: also write <home>/.mcp.json."""
    cfg = config or config_path()
    data = load_config_file(cfg)
    entries = {}
    if remove:
        new, gone = strip(data)
        res = {"removed": gone}
    else:
        entries = build_entries(home, python=python, servers=servers, run_id=run_id, ceiling=ceiling)
        if serum is not None:
            entries.update(serum_entry(home, **serum))
        new, res = merge(data, entries)
    changed = new != data
    bak = None
    if changed and not dry_run:
        bak = write_atomic(cfg, new)
    stale = []
    if config is None:                                       # entries left in a file Claude Desktop never reads
        for other in unused_config_paths():
            try:
                od = load_config_file(other)
            except ValueError:
                continue
            nd, gone = strip(od)
            if gone:
                stale.append({"file": str(other), "removed": gone})
                if not dry_run:
                    write_atomic(other, nd)
    out = {"config": str(cfg), "dry_run": dry_run, "changed": changed, "backup": str(bak) if bak else None, "result": res, "stale": stale,
           "servers": sorted(k for k in new.get("mcpServers", {}) if k.startswith(PREFIX)), "others_kept": sorted(k for k in new.get("mcpServers", {}) if not k.startswith(PREFIX))}
    if claude_code and entries:
        out["claude_code"] = claude_code_file(home, entries, dry_run)
    return out


def render(r: dict) -> str:
    lines = ["Claude Desktop config: %s" % r["config"]]
    for k, v in r["result"].items():
        if v:
            lines.append("  %s: %s" % (k, ", ".join(v)))
    if r["others_kept"]:
        lines.append("  other servers kept as they were: %s" % ", ".join(r["others_kept"]))
    for s in r.get("stale", []):
        lines.append("  removed old entries from %s, a file Claude Desktop does not read: %s" % (s["file"], ", ".join(s["removed"])))
    if r.get("claude_code"):
        cc = r["claude_code"]
        lines.append("Claude Code project file: %s (%s)" % (cc["file"], "updated" if cc["changed"] else "already up to date"))
    if r["dry_run"]:
        lines.append("DRY RUN: nothing was written.")
    elif r["changed"]:
        if r["backup"]:
            lines.append("Backup of the old file: %s" % r["backup"])
        first = {"closed": "Claude Desktop is closed: start it and it loads the servers.",
                 "loaded": "Claude Desktop was opened after the file was written, so it has loaded the servers.",
                 "custom": "This is not Claude Desktop's own file (--config): nothing else to do here."}.get(
            r.get("desktop"), "Now fully quit Claude Desktop (tray icon or Task Manager, not just the window) and start it again.")
        lines += ["", first,
                  "The servers then appear under Settings > Developer. Logs: %s" % (log_dir(Path(r["config"])) / "mcp-server-<name>.log"),
                  "In a new chat the first call is list_skills (fl-bridge): it serves the co-producer's skills and docs."]
    else:
        lines.append("Nothing to change.")
    return "\n".join(lines)


def ask_and_install(home: Path, ask=input, out=print, **kw) -> dict | None:
    """Used by `coproducer setup`: asks once, installs the three default servers on yes. Returns None when declined or not interactive."""
    try:
        if not sys.stdin.isatty() and ask is input:
            return None
        ans = ask("Add the coproducer MCP servers to Claude Desktop? [y/N] ").strip().lower()
    except EOFError:
        return None
    if ans not in ("y", "yes"):
        out("Skipped. Later:  coproducer install-desktop")
        return None
    try:
        r = install(home, **kw)
    except ValueError as e:
        out(str(e))
        return None
    out(render(r))
    return r
