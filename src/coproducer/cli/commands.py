"""One function per subcommand: cmd_<name>(home, args, out) -> exit code. Kept thin; the work lives in the sibling modules."""
from __future__ import annotations

import json
import runpy
from pathlib import Path

from ..config import load_config


def cmd_setup(home, a, out):
    from .setup_cmd import apply_settings, render_report, run_setup
    out(render_report(run_setup(home, a.fl_exe, a.data_dir)))
    changed = apply_settings(home, getattr(a, "torch_index", None), getattr(a, "models_dir", None))
    if changed:
        out("config.toml: " + "; ".join(changed))
    if not getattr(a, "no_desktop", False):
        from . import desktop_cmd
        if getattr(a, "desktop", False):
            try:
                out("\nSTEP E. Claude Desktop\n" + desktop_cmd.render(desktop_cmd.install(home)))
            except ValueError as e:
                out(str(e))
                return 1
        else:
            out("")
            desktop_cmd.ask_and_install(home, out=out)
    return 0


def cmd_install_desktop(home, a, out):
    from . import desktop_cmd
    servers = tuple(a.servers) if a.servers else desktop_cmd.DEFAULT_SERVERS
    if a.with_desktop_control and "desktop-control" not in servers:
        servers += ("desktop-control",)
    serum = ({"uv": a.uv, "presets": Path(a.serum_presets) if a.serum_presets else None,
              "sample_bank": Path(a.sample_bank) if a.sample_bank else None} if getattr(a, "with_serum", False) else None)
    kw = dict(config=Path(a.config) if a.config else None, servers=servers, run_id=a.run_id, ceiling=a.ceiling, python=a.python,
              remove=a.remove, serum=serum, claude_code=getattr(a, "claude_code", False))
    try:
        desktop_cmd.install(home, dry_run=True, **kw)            # every check (paths, JSON, serum-mcp) before anything waits or writes
    except ValueError as e:
        out(str(e))
        return 1
    import time
    own = a.config is None and not a.dry_run
    first = None
    for attempt in range(3):
        if own and not getattr(a, "force", False) and desktop_cmd.desktop_processes():
            if not getattr(a, "wait", False):
                out(desktop_cmd.RUNNING_HELP)
                return 2
            if not desktop_cmd.wait_for_quit(a.wait_minutes, out):
                out("Claude Desktop is still running; nothing was written. " + desktop_cmd.RUNNING_HELP)
                return 3
        try:
            r = desktop_cmd.install(home, dry_run=a.dry_run, **kw)
        except ValueError as e:
            out(str(e))
            return 1
        written = time.time()
        if first is None:
            first = r
        elif first["changed"] and not r["changed"]:            # a later pass found the file as the first one left it
            r = {**r, "changed": True, "result": first["result"], "backup": first["backup"]}
        # A Claude Desktop that started before the write finished read the old file and will write it back: go round again.
        early = [t for t in desktop_cmd.desktop_start_times() if t <= written] if own and not getattr(a, "force", False) else []
        if not early:
            break
        out("Claude Desktop was opened again before the servers were written, so it read the old file. Quit it once more and leave it closed.")
        if not getattr(a, "wait", False):
            return 4
    else:
        out("Claude Desktop kept being reopened before the file could be written; run this again when it can stay closed for a few seconds.")
        return 4
    if a.config:
        r["desktop"] = "custom"
    elif a.dry_run or getattr(a, "force", False):
        r["desktop"] = "running" if desktop_cmd.desktop_processes() else "closed"
    else:
        r["desktop"] = "loaded" if desktop_cmd.desktop_processes() else "closed"      # running now means it started after the write
    out(desktop_cmd.render(r))
    if getattr(a, "restart", False) and not a.dry_run and a.config is None and r["desktop"] == "closed":
        started = desktop_cmd.start_desktop()
        out("Started Claude Desktop again (%s); the co-producer servers load as it starts." % started if started
            else "Start Claude Desktop again yourself; the co-producer servers load as it starts.")
    return 0


def cmd_doctor(home, a, out):
    from .doctor import render, run_checks
    rows = run_checks(home)
    out(render(rows))
    return 1 if any(r["status"] == "fail" for r in rows) else 0


def cmd_install_models(home, a, out):
    from .models_cmd import install, render
    rows = install(home, a.names, a.dry_run, weights_only=a.weights_only, with_optional=getattr(a, "with_optional", False))
    out(render(rows))
    return 1 if any(r["status"].startswith("failed") for r in rows.values()) else 0


def cmd_install_host(home, a, out):
    import subprocess

    from .deps_cmd import host_install_plan
    plan = host_install_plan(home)
    if not plan:
        out("no dependency lock found; run coproducer deps --freeze on a working machine first")
        return 1
    for argv, cwd in plan:
        out(" ".join(argv))
        if not a.dry_run:
            code = subprocess.run(argv, cwd=cwd).returncode
            if code:
                out("failed (exit %d)" % code)
                return code
    return 0


def cmd_deps(home, a, out):
    from . import deps_cmd
    cfg = load_config(home)
    if a.freeze:
        lock = deps_cmd.freeze(home, cfg)
        out("locked %d host packages, %d tools, %d ollama models, %d model environments" % (len(lock["host"]), len(lock["tools"]), len(lock["ollama"]), len(lock["envs"])))
    if a.freeze or a.docs:
        lock = deps_cmd.load_lock(home)
        if lock is None:
            out("no lock yet; run coproducer deps --freeze")
            return 1
        (home / "docs").mkdir(exist_ok=True)
        (home / "docs" / "DEPENDENCIES.md").write_text(deps_cmd.render_docs(lock), encoding="utf-8", newline="\n")
        out("wrote docs/DEPENDENCIES.md")
        return 0
    rows = deps_cmd.check(home, cfg)
    out(deps_cmd.render_check(rows))
    return 1 if any(r["status"] == "fail" for r in rows) else 0


def cmd_halt(home, a, out):
    from .. import halt_key
    if a.clear:
        out("HALT cleared" if halt_key.clear(home) else "nothing was halted")
        return 0
    if a.key:
        try:
            halt_key.listen(home, say=out)
        except OSError as e:
            out("cannot watch the halt key: %s" % e)
            return 1
        return 0
    out("halted: %s  (clear with: coproducer halt --clear)" % halt_key.trip(home, "coproducer halt"))
    return 0


def cmd_lint(home, a, out):
    from ..lint import lint_tree
    problems = lint_tree(home / "modules")
    for mod, items in sorted(problems.items()):
        for item in items:
            out("%s: %s" % (mod, item))
    out("%s" % ("lint clean" if not problems else "%d module(s) with problems" % len(problems)))
    return 1 if problems else 0


def cmd_gen(home, a, out):
    codes = []
    for tool in ("gen_fl_side.py", "gen_inventory.py"):
        f = home / "tools" / tool
        if f.is_file():
            try:
                runpy.run_path(str(f), run_name="__main__")
            except SystemExit as e:
                codes.append(e.code or 0)
    from ..skillsgen import generate
    out("skill catalogs: %d files" % len(generate(home)))
    return 1 if any(codes) else 0


def cmd_serve(home, a, out):
    from ..servers import common
    common.main(a.server, ["--home", str(home), *[x for x in a.rest if x != "--"]])
    return 0


def cmd_new_project(home, a, out):
    from .project_cmd import new_project
    r = new_project(home, a.name, a.mode, a.source)
    out(r["message"])
    return 0 if r["ok"] else 1


def _run(home, a, out, plan, run_id):
    from .run_cmd import execute
    code, text = execute(home, run_id, plan, Path(a.spec) if a.spec else None, a.unattended, a.ceiling)
    out(text)
    return code


def cmd_run(home, a, out):
    from .run_cmd import load_plan_file
    return _run(home, a, out, load_plan_file(Path(a.plan)), a.run_id)


def cmd_resume(home, a, out):
    return _run(home, a, out, None, a.run_id)


def cmd_promote(home, a, out):
    from .project_cmd import promote
    out("This copies %s over %s. The old file is kept as a backup. Type the word promote to continue." % (a.result, a.destination))
    r = promote(home, a.run_id, Path(a.result), Path(a.destination), input("> ").strip())
    out(r["message"])
    return 0 if r["ok"] else 1


def cmd_calibrate(home, a, out):
    from .calibrate_cmd import available, calibrate
    if not available():
        out("calibrate needs Windows with FL Studio open")
        return 1
    calibrate(home, a.anchors, out=out)
    return 0


def _session_call(home):
    from ..servers.common import make_session
    s = make_session(home, "probe", "fl-bridge")
    return s, s.registry.call


def _probe_report(home, cfg, s, a, out, p):
    """Run the probes inside FL over the bridge, save the raw report, print the summary."""
    from ..bridge import BridgeClient
    from ..midi_transport import open_midi_transport
    opened = open_midi_transport(cfg["midi"]["out"], cfg["midi"]["in"])
    if not opened.ok:
        out(opened.error.message)
        return 1
    client = BridgeClient(s.registry, opened.value, max_payload=cfg["bridge"]["max_payload"])
    report = p.collect_report(client, mutating=a.mutating, probe_args={"file_io": {"dirs": [str(home / "sandbox")]}})
    if "_error" in report:
        out("the bridge did not answer: %s. Run: coproducer probe ping" % report["_error"])
        return 1
    dest = home / "sandbox" / "probe_report.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, indent=1, sort_keys=True), encoding="utf-8")
    inv = home / "src" / "coproducer" / "data" / "api_inventory.json"
    out(p.summarize_report(report, json.loads(inv.read_text(encoding="utf-8")) if inv.is_file() else {}))
    out("full report: %s" % dest)
    return 0


def _probe_stress(home, cfg, a, out):
    """Live bridge stress test (read-only); saves sandbox/stress_live.json."""
    from ..bridge import BridgeClient
    from ..midi_transport import open_midi_transport
    from . import stress_cmd
    s, _ = _session_call(home)
    opened = open_midi_transport(cfg["midi"]["out"], cfg["midi"]["in"])
    if not opened.ok:
        out(opened.error.message)
        return 1
    client = BridgeClient(s.registry, opened.value, max_payload=cfg["bridge"]["max_payload"])
    client.attach(s.registry)
    if not stress_cmd.alive(client):
        out("the bridge did not answer: run  coproducer probe ping  first")
        return 1
    only = [x for x in a.only.split(",") if x]
    rows = stress_cmd.run_all(client, s.registry, opened.value, [x for x in only if x != "desktop"] or ([] if not only else ["none"]))
    if "desktop" in only:
        rows += stress_cmd.desktop_weird(s.registry.call)
    if not only:
        opened.value.close()
        rows.append(stress_cmd.reconnect(open_midi_transport, cfg, lambda t: BridgeClient(s.registry, t, max_payload=cfg["bridge"]["max_payload"]), None))
    dest = home / "sandbox" / "stress_live.json"
    dest.write_text(json.dumps(rows, indent=1, default=str), encoding="utf-8")
    out(stress_cmd.render(rows))
    out("full report: %s" % dest)
    return 0 if all(r["passed"] for r in rows) else 1


def cmd_probe(home, a, out):
    from . import probe_cmd as p
    cfg = load_config(home)
    data = p.where_is_data(cfg)
    if a.which == "install-fl":
        out("installed %s (legacy). FL scripts cannot write files, so the report file will not appear; use  coproducer probe report  instead, which asks the running bridge." % p.install_fl(home, data, a.mutating))
        return 0
    if a.which == "stress":
        return _probe_stress(home, cfg, a, out)
    s, call = _session_call(home)
    # the person running a probe command is the approval for its A1 steps: the local critic, and closing FL around a render
    s.approved_now = frozenset({"critique_audio", "render_with_restart"})
    if a.which == "models":
        res = p.models(call, home / "sandbox" / "probe_models")
    elif a.which == "report":
        return _probe_report(home, cfg, s, a, out, p)
    elif a.which in ("ping", "throughput"):
        from ..servers.common import attach_bridge
        from ..bridge import BridgeClient
        from ..midi_transport import open_midi_transport
        opened = open_midi_transport(cfg["midi"]["out"], cfg["midi"]["in"])
        if not opened.ok:
            out(opened.error.message)
            return 1
        client = BridgeClient(s.registry, opened.value, max_payload=cfg["bridge"]["max_payload"])
        res = p.ping(client) if a.which == "ping" else p.throughput(client)
    elif a.which in ("apply", "listen", "vibe", "eq", "polish", "numbering"):
        from ..servers.common import attach_bridge
        warn = attach_bridge(s, cfg["midi"]["out"], cfg["midi"]["in"], cfg["bridge"]["max_payload"])
        if warn:
            out(warn)
            return 1
        if a.which == "numbering":
            from . import numbering_cmd
            res = numbering_cmd.numbering(call)
        elif a.which == "polish":
            from . import polish_cmd
            res = polish_cmd.polish(call, Path(a.project), home / "sandbox" / "polish", a.bpm, a.keep)
        elif a.which == "eq":
            from . import eq_cmd
            res = eq_cmd.eq_calibration(call, Path(a.project), home / "sandbox" / "eq", values=tuple(float(v) for v in a.eq_values.split(",")))
        elif a.which == "vibe":
            from . import vibe_cmd
            res = vibe_cmd.vibe(call, Path(a.project), home / "sandbox" / "vibe", a.prompt, a.bpm, a.duration, a.track, a.adjust, a.keep)
        elif a.which == "listen":
            res = p.listen(call, Path(a.project), home / "sandbox" / "listen")
        else:
            res = p.apply(call, Path(a.project), home / "sandbox" / "apply")
    elif a.which == "critique":
        res = p.critique(call, Path(a.project))
    elif a.which == "loop":
        res = p.loop(call, home / "sandbox" / "loop")
    elif a.which == "brain":
        res = p.brain(call)
    elif a.which == "render":
        res = p.render(call, Path(a.project), Path(a.project).parent / "render_probe")
    else:
        res = p.desktop(call)
    out(json.dumps(res, indent=1))
    return 0 if res.get("passed") else 1


def cmd_check_cards(home, a, out):
    from ..cards.parse import validate_card
    bad = 0
    for f in sorted((home / "cards").rglob("*.card.md")):
        problems = validate_card(f.read_text(encoding="utf-8").replace("Card NN", "Card 99"))
        bad += bool(problems)
        out("%s: %s" % (f.relative_to(home), "ok" if not problems else "; ".join(problems)))
    return 1 if bad else 0


def cmd_build_card(home, a, out):
    from ..cards.build import build_card, calibration_summary, save_result
    s, results = _session_call(home)[0], []

    def ask(system, user):
        r = s.registry.call("call_agent_llm", prompt=user, system=system, temperature=0.2, max_tokens=4096)
        if not r.ok:
            raise RuntimeError(r.error.message)
        return r.value["message"]["content"]

    for name in a.cards:
        res = build_card(Path(name).read_text(encoding="utf-8"), ask, home / "modules", a.tries)
        results.append(res)
        where = save_result(res, home / a.out) if res["name"] else None
        out("%s: %s after %d attempt(s)%s" % (res["name"] or name, "PASSED" if res["passed"] else "failed", len(res["attempts"]),
                                             "  -> %s (review, then copy into modules/)" % where if res["passed"] else
                                             "  last: %s" % (res["attempts"][-1]["report"][-300:] if res["attempts"] else res.get("problems"))))
    out(json.dumps(calibration_summary(results)))
    return 0 if all(r["passed"] for r in results) else 1


def cmd_check_servers(home, a, out):
    from . import desktop_cmd, servers_check
    cfg = Path(a.config) if a.config else desktop_cmd.config_path()
    rows = servers_check.check(cfg)
    out(servers_check.render(rows, cfg))
    return 0 if rows and all(r["ok"] for r in rows) else 1


def cmd_setup_midi(home, a, out):
    from ..procs import Procs
    from . import midi_setup
    n = Procs().fl_count()
    return midi_setup.run(n != 0, out, start_loopmidi=not a.no_start)


def cmd_remix(home, a, out):
    import sys
    tool = home / "tools" / "remix_song.py"
    if not tool.is_file():
        out("no tools/remix_song.py under %s" % home)
        return 1
    sys.argv = [str(tool)] + list(a.rest)
    try:
        runpy.run_path(str(tool), run_name="__main__")
    except SystemExit as e:
        return int(e.code or 0) if not isinstance(e.code, str) else (out(e.code) or 1)
    return 0
