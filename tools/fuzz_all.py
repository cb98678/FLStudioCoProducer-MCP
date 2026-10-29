"""Fuzz every module on the fake FL and write a JSON report.

  python tools/fuzz_all.py [--out report.json] [--only name,name] [--chaos N] [--bare]

--bare runs with no services configured (the machine before setup). Exit code 1 when any defect is found."""
from __future__ import annotations

import argparse
import json
import random
import sys
import os
import tempfile
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from coproducer import fuzz  # noqa: E402


def stall_watchdog(state: dict, limit_s: float) -> None:
    """A fuzz run must never freeze the machine's job queue: when no module finishes for limit_s seconds, say where and exit."""
    def watch() -> None:
        while True:
            time.sleep(5)
            if time.time() - state["last"] > limit_s:
                print("STALLED for %.0f s inside %s: exiting so the queue is not blocked" % (time.time() - state["last"], state["module"]), flush=True)
                os._exit(3)
    threading.Thread(target=watch, daemon=True).start()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="fuzz_report.json")
    ap.add_argument("--only", default="")
    ap.add_argument("--chaos", type=int, default=25)
    ap.add_argument("--bare", action="store_true")
    ap.add_argument("--timeout", type=float, default=fuzz.TIMEOUT_S)
    ap.add_argument("--stall", type=float, default=240.0, help="exit when no module finishes in this many seconds")
    a = ap.parse_args()
    t0, outcomes, state = time.time(), [], {"last": time.time(), "module": "start"}
    stall_watchdog(state, a.stall)
    with tempfile.TemporaryDirectory(prefix="coproducer_fuzz_") as tmp:
        w = fuzz.build_world(Path(tmp), fully=not a.bare)
        names = [n for n in w.reg.names() if not a.only or n in a.only.split(",")]
        try:
            for i, name in enumerate(names, 1):
                state.update(last=time.time(), module=name)
                outs = fuzz.fuzz_module(w, name, random.Random(fuzz.SEED), a.timeout, a.chaos)
                outcomes += outs
                bad = sum(o.status == "defect" for o in outs)
                print("%3d/%d %-40s %5d calls  %d defects" % (i, len(names), name, len(outs), bad), flush=True)
                Path(a.out + ".partial").write_text(json.dumps(fuzz.summarize(outcomes), indent=1), encoding="utf-8")
                # a fresh fake FL per module so one module's damage cannot hide or cause another's
                fuzz.close_world(w)
                w = fuzz.build_world(Path(tmp), fully=not a.bare)
        finally:
            fuzz.close_world(w)
    summary = fuzz.summarize(outcomes)
    rep = {"seconds": round(time.time() - t0, 1), "world": "bare" if a.bare else "full", "modules": len(summary), "calls": len(outcomes),
           "defects": sum(o.status == "defect" for o in outcomes), "fragile": sum(o.status == "fragile" for o in outcomes),
           "by_module": summary}
    Path(a.out).write_text(json.dumps(rep, indent=1), encoding="utf-8")
    print("%d modules, %d calls, %d defects, %d fragile, %.0f s -> %s" % (rep["modules"], rep["calls"], rep["defects"], rep["fragile"], rep["seconds"], a.out))
    return 1 if rep["defects"] else 0


if __name__ == "__main__":
    sys.exit(main())
