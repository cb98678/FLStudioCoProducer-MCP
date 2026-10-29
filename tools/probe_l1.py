"""Call every read-only L1 op once through the live bridge and report which run in this FL build, so the generated ops are checked on the real API.

    python tools/probe_l1.py [--out sandbox\\probe_l1.json] [--only mixer,channels] [--launch SANDBOX_PROJECT.flp]

FL must be running with the Coproducer controller script and a sandbox project open, or with --launch, closed: the tool then starts FL on that
sandbox project, waits for the bridge, probes, and closes the FL it started (gracefully; an FL the person opened is never closed). Only ops whose manifest says reads_fl are called, each with
the sample arguments of its generated test; nothing is written. An op that answers ok, or answers E_ARG for an index the open project does not
have, exists and works; E_INTERNAL or E_UNSUPPORTED_API marks a function this build does not have or that fails.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
import time
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from coproducer.config import load_config  # noqa: E402
from coproducer.servers.common import attach_bridge, make_session  # noqa: E402

HOME = Path(__file__).resolve().parents[1]


def sample_args(op_dir: Path) -> tuple:
    test = (op_dir / ("test_%s.py" % op_dir.name)).read_text(encoding="utf-8")
    line = next(ln for ln in test.splitlines() if ln.startswith("SAMPLE = "))
    return ast.literal_eval(line.split("=", 1)[1].strip())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HOME / "sandbox" / "probe_l1.json"))
    ap.add_argument("--only", default="")
    ap.add_argument("--launch", default="", help="a sandbox project to start FL on when FL is closed")
    a = ap.parse_args()
    s = make_session(HOME, "probe_l1", "fl-bridge", "A2")
    cfg = load_config(HOME)
    started = False
    if a.launch:
        from coproducer.procs import Procs
        from coproducer.services import get_service
        procs = Procs()
        if "sandbox" not in [x.lower() for x in Path(a.launch).resolve().parts]:
            print("refusing to open a project outside the sandbox")
            return 1
        if procs.fl_count() == 0:
            procs.launch(str(get_service("fl_exe")), a.launch)
            started = True
            print("started FL on", a.launch, flush=True)
    warn = attach_bridge(s, cfg["midi"]["out"], cfg["midi"]["in"], cfg["bridge"]["max_payload"])
    deadline = time.monotonic() + 150
    while warn is None and time.monotonic() < deadline and not s.registry.call("ping_fl").ok:
        time.sleep(3)
    if warn or not s.registry.call("ping_fl").ok:
        print(warn or "the bridge did not answer")
        return 1
    only = set(filter(None, a.only.split(",")))
    rows = []
    for d in sorted((HOME / "modules" / "l1_fl_ops").glob("op_*")):
        man = tomllib.loads((d / "module.toml").read_text(encoding="utf-8"))
        if man["policy"]["side_effect"] != "reads_fl" or (only and d.name.split("_")[1] not in only):
            continue
        schema = json.loads(man["io"]["input"])
        names = list(schema.get("properties", {}))
        args = dict(zip(names, sample_args(d)))
        r = s.registry.call(d.name, **args)
        rows.append({"op": d.name, "args": args, "ok": r.ok, "code": None if r.ok else r.error.code,
                     "message": None if r.ok else r.error.message[:160], "value": repr(r.value)[:80] if r.ok else None})
        print("%-48s %s" % (d.name, "ok" if r.ok else "%s %s" % (r.error.code, r.error.message[:80])), flush=True)
    Path(a.out).write_text(json.dumps(rows, indent=1), encoding="utf-8")
    good = sum(1 for r in rows if r["ok"] or r["code"] == "E_ARG")
    print("ran %d read ops: %d answered (ok or argument errors), %d failed" % (len(rows), good, len(rows) - good))
    if started:
        from coproducer.procs import Procs
        print("closed the FL it started" if Procs().close_fl(30.0) else "FL did not close (a dialog may be open)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
