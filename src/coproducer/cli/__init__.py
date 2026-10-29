"""The `coproducer` command line. Each subcommand is a thin wrapper over a function in this package."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

COMMANDS = ("setup", "install-desktop", "check-servers", "setup-midi", "remix", "doctor", "install-models", "install-host", "deps", "lint", "gen", "serve", "new-project", "run", "resume", "promote", "calibrate", "probe", "check-cards", "build-card", "halt")


def default_home() -> str:
    """COPRODUCER_HOME (the installer sets it), else the checkout this package runs from (an editable install), else the current folder."""
    if os.environ.get("COPRODUCER_HOME"):
        return os.environ["COPRODUCER_HOME"]
    repo = Path(__file__).resolve().parents[3]
    return str(repo) if (repo / "pyproject.toml").is_file() and (repo / "modules").is_dir() else "."


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="coproducer", description="Local-first AI co-producer for FL Studio")
    p.add_argument("--home", default=default_home(), help="folder holding modules/, config.toml, sandbox/ and runs/ (default: COPRODUCER_HOME, else this install)")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("setup", help="create folders and config.toml, install the FL-side script, print the MIDI steps")
    s.add_argument("--fl-exe", default=None)
    s.add_argument("--data-dir", default=None)
    g = s.add_mutually_exclusive_group()
    g.add_argument("--desktop", action="store_true", help="also register the MCP servers with Claude Desktop, without asking")
    g.add_argument("--no-desktop", action="store_true", help="do not ask about Claude Desktop")
    s.add_argument("--torch-index", default=None, help="set [gpu] torch_index (the PyTorch wheel index for this GPU; empty for CPU)")
    s.add_argument("--models-dir", default=None, help="set [paths] models and weights to a folder outside the install (environments and weights)")
    idk = sub.add_parser("install-desktop", help="add the MCP servers to Claude Desktop's claude_desktop_config.json (keeps your other servers)")
    idk.add_argument("--config", default=None, help="config file to edit (default: the Claude Desktop location for this OS)")
    idk.add_argument("--servers", nargs="+", default=None, choices=["fl-bridge", "studio-audio", "studio-ml", "desktop-control"], help="default: fl-bridge studio-audio studio-ml")
    idk.add_argument("--with-desktop-control", action="store_true", help="also register desktop-control (clicks in the FL window; off by default)")
    idk.add_argument("--run-id", default="default")
    idk.add_argument("--ceiling", default="A2", choices=["A0", "A1", "A2"], help="autonomy ceiling for desktop-control")
    idk.add_argument("--python", default=None, help="interpreter to run the servers with (default: the one running this command)")
    idk.add_argument("--dry-run", action="store_true", help="show what would change, write nothing")
    idk.add_argument("--remove", action="store_true", help="remove the coproducer-* entries again")
    idk.add_argument("--with-serum", action="store_true", help="also register the third-party serum-mcp server from sandbox\\third_party\\serum-mcp (Serum 2 presets)")
    idk.add_argument("--serum-presets", default=None, help="Serum 2 user preset folder (default: Documents\\Xfer\\Serum 2 Presets\\Presets\\User)")
    idk.add_argument("--sample-bank", default=None, help="your own sample library for serum-mcp's sample tools (optional)")
    idk.add_argument("--uv", default=None, help="uv executable for serum-mcp (default: the one on PATH)")
    idk.add_argument("--claude-code", action="store_true", help="also write the same servers to .mcp.json in the home folder, for Claude Code")
    idk.add_argument("--wait", action="store_true", help="if Claude Desktop is running, wait until you quit it, then write (it rewrites the file while it runs)")
    idk.add_argument("--wait-minutes", type=float, default=30.0, help="how long --wait waits (default 30)")
    idk.add_argument("--restart", action="store_true", help="start Claude Desktop again after writing")
    idk.add_argument("--force", action="store_true", help="write even while Claude Desktop is running (it may undo this when one of its settings changes)")
    sub.add_parser("doctor", help="check this machine and the repo")
    m = sub.add_parser("install-models", help="create model environments (uses uv)")
    m.add_argument("names", nargs="*")
    m.add_argument("--dry-run", action="store_true")
    m.add_argument("--weights-only", action="store_true", help="only download weights of stacks that have them")
    m.add_argument("--with-optional", action="store_true", help="also the downloads only optional tools need (the Music Flamingo critic, about 16 GB; MuQ-MuLan)")
    cs = sub.add_parser("check-servers", help="start each coproducer server as Claude Desktop will and list its tools")
    cs.add_argument("--config", default=None)
    sm = sub.add_parser("setup-midi", help="Windows: create the loopMIDI ports and set FL Studio's MIDI settings for the bridge (FL must be closed)")
    sm.add_argument("--no-start", action="store_true", help="do not start loopMIDI now")
    rx = sub.add_parser("remix", help="remix a song end to end (tools/remix_song.py; coproducer remix --help for its options)", add_help=False)
    rx.add_argument("rest", nargs=argparse.REMAINDER)
    ih = sub.add_parser("install-host", help="build the host venv from requirements.lock (uses uv)")
    ih.add_argument("--dry-run", action="store_true")
    d = sub.add_parser("deps", help="check this machine against the dependency lock, or write it")
    d.add_argument("--freeze", action="store_true", help="write the lock and requirements.lock from THIS machine (use a machine where everything works)")
    d.add_argument("--docs", action="store_true", help="regenerate docs/DEPENDENCIES.md from the lock")
    sub.add_parser("lint", help="lint every module")
    sub.add_parser("gen", help="regenerate the FL-side script and the API inventory")
    v = sub.add_parser("serve", help="run one MCP server over stdio")
    v.add_argument("server", choices=["fl-bridge", "studio-audio", "studio-ml", "desktop-control"])
    v.add_argument("rest", nargs=argparse.REMAINDER)
    n = sub.add_parser("new-project", help="create a spec sheet in specs/")
    n.add_argument("name")
    n.add_argument("--mode", choices=["new", "restyle", "mix", "master"], default="new")
    n.add_argument("--source", default=None, help="the original project or audio file")
    for name in ("run", "resume"):
        r = sub.add_parser(name, help=("run a plan file" if name == "run" else "continue a stopped run from its ledger"))
        r.add_argument("plan" if name == "run" else "run_id")
        r.add_argument("--run-id", default="default")
        r.add_argument("--spec", default=None)
        r.add_argument("--unattended", action="store_true", help="leave questions in pending_decisions.json instead of asking")
        r.add_argument("--ceiling", default="A2", choices=["A0", "A1", "A2"])
    pr = sub.add_parser("promote", help="HUMAN ONLY: copy a sandbox result over a real project file")
    pr.add_argument("result")
    pr.add_argument("destination")
    pr.add_argument("--run-id", default="default")
    c = sub.add_parser("calibrate", help="record click anchors for GUI recipes (Windows)")
    c.add_argument("anchors", nargs="+")
    h = sub.add_parser("halt", help="stop every run now (writes runs/HALT), clear it, or watch the global halt key")
    h.add_argument("--clear", action="store_true", help="remove the HALT files so runs can start again")
    h.add_argument("--key", action="store_true", help="Windows: watch Ctrl+Alt+F12 and halt when it is pressed (leave the window open)")
    sub.add_parser("check-cards", help="validate every task card in cards/")
    bc = sub.add_parser("build-card", help="give task cards to the local LLM (config [llm]) and gate what it writes")
    bc.add_argument("cards", nargs="+")
    bc.add_argument("--tries", type=int, default=3)
    bc.add_argument("--out", default="build")
    pb = sub.add_parser("probe", help="Gate 0 checks that need a real machine")
    pb.add_argument("which", choices=["install-fl", "report", "ping", "throughput", "render", "brain", "loop", "apply", "desktop", "models", "critique", "listen", "vibe", "eq", "polish", "numbering", "stress"])
    pb.add_argument("--mutating", action="store_true", help="report: also test writes (fader, undo, marker) inside FL; use on a scratch project only")
    pb.add_argument("--project", default=None, help="render, apply, listen, vibe: a saved project inside the sandbox, open in FL")
    pb.add_argument("--prompt", default="driving techno loop, dark, punchy kick, rolling bassline", help="vibe: what to generate")
    pb.add_argument("--track", type=int, default=1, help="vibe: playlist track for the clip (use a free one)")
    pb.add_argument("--adjust", action="store_true", help="vibe: also apply the brain's gain and EQ proposals and check them against a second render")
    pb.add_argument("--keep", action="store_true", help="polish: leave the applied changes in the sandbox project (default: put everything back)")
    pb.add_argument("--only", default="", help="stress: comma list of scenarios (latency,reads,args,payload,ops,wrap,stale,threads,garbage,stalls (150 s of steady pings that times every FL freeze); desktop; desktop minimizes FL and opens Notepad briefly, so it only runs when named)")
    pb.add_argument("--bpm", type=float, default=128.0)
    pb.add_argument("--eq-values", default="0.65,0.8", help="eq: the EQ values (0 to 1, 0.5 flat) to test on each band")
    pb.add_argument("--duration", type=float, default=10.0, help="vibe: seconds of audio to generate")
    return p


def _out(text: str) -> None:
    print(text, flush=True)          # flushed: the installer shows a command's lines as they come (a pipe would hold them back)


def use_installed_tools(home: Path, env=None) -> list:
    """install.ps1 keeps its own uv, ffmpeg and Python under <home>/runtime. Put them first on PATH for this process and everything it starts
    (model environments, ffmpeg conversions), so the servers Claude Desktop launches find them without the user's PATH. Returns the folders."""
    env = os.environ if env is None else env
    rt = Path(home) / "runtime"
    have = env.get("PATH", "").split(os.pathsep)
    dirs = [str(d) for d in (rt / "uv", rt / "ffmpeg" / "bin") if d.is_dir() and str(d) not in have]
    if dirs:
        env["PATH"] = os.pathsep.join(dirs + [env.get("PATH", "")])
    if (rt / "python").is_dir():
        env.setdefault("UV_PYTHON_INSTALL_DIR", str(rt / "python"))
        env.setdefault("UV_MANAGED_PYTHON", "1")          # environments made later use uv's Pythons too, as the installer's did
    return dirs


def dispatch(a: argparse.Namespace) -> int:
    from . import commands
    home = Path(a.home).resolve()
    use_installed_tools(home)
    return getattr(commands, "cmd_" + a.cmd.replace("-", "_"))(home, a, _out)


def main(argv: list | None = None) -> int:
    code = dispatch(build_parser().parse_args(argv))
    sys.exit(code) if argv is None else None
    return code
