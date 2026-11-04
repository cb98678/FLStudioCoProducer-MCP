"""Run FL's Newtime on a vocal's chunks, or Newtone on a vocal file, in a fresh FL started on a bench project at the vocal's tempo.

    python tools/vocal_gui_run.py chunks  --manifest CHUNKS.json --bench BENCH.flp [--lead -1] [--passes 2] [--target-ms 10] [--indices 3,4] [--max-move 0.1]
    python tools/vocal_gui_run.py newtone --in VOCAL.wav --out TUNED.wav --bench BENCH.flp [--style middle] [--midi TUNED.mid]
    python tools/vocal_gui_run.py bench   --from sandbox/gui_work/gtm_vocal_bench_130.flp --out BENCH.flp --bpm 117.5

The bench is any project with an audio clip at the start of playlist track 1 (Newtime and Newtone open from its clip menu); `bench`
copies one and sets its tempo, which must be the vocal file's own tempo (at another tempo Newtime draws the tempo-synced sample
stretched to the project and the markers match nothing, LESSONS row 129). FL must be closed before a run: a running FL is reported, never
killed (the person may have unsaved work); the run's FL is killed afterwards, and FL's command-line render needs it closed anyway.
Set --keep to leave FL open for a look. Writes RUN.log.json beside the manifest or the output. Every run also saves its sessions as FL projects
(sessionflp: one per chunk under the song's projects/newtime, the Newtone session under projects/newtone) so they can be opened and adjusted by
hand later; --projects DIR moves them, --no-projects skips them. Skill vocal-chunking has the steps.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "src"))
from coproducer import sessionflp  # noqa: E402


def _session(run_id: str):
    from coproducer.result import fail, ok
    from coproducer.servers.common import make_session
    from coproducer.services import get_service

    s = make_session(HOME, run_id, "fl-bridge", "A2")
    get_service("desktop_config")["allow_unverified"] = True
    s.collab = type("Yes", (), {"approve": lambda self, w, d: ok(True), "ask": lambda self, q, o: fail("E_PENDING_HUMAN", q)})()
    return s


def _start_fl(s, bench: Path) -> bool:
    from coproducer.servers.common import attach_bridge
    from coproducer.services import get_service

    procs, exe = get_service("procs"), get_service("fl_exe")
    if procs.fl_count():
        print("FL is already running: close it (or save your work) and run again; nothing was touched", flush=True)
        return False
    procs.launch(exe, str(bench))
    print("launched FL on", bench.name, flush=True)
    time.sleep(25)
    attach_bridge(s, "coproducer-in", "coproducer-out")
    for _ in range(40):
        if s.registry.call("ping_fl").ok:
            print("FL up", flush=True)
            time.sleep(6)
            return True
        time.sleep(3)
    print("FL did not answer the bridge", flush=True)
    return False


def _stop_fl() -> None:
    subprocess.run(["taskkill", "/F", "/IM", "FL64.exe"], capture_output=True)
    time.sleep(4)


def _projects_dir(a) -> Path | None:
    """Where the sessions are saved as FL projects: --projects, else the song's projects folder beside the bench's folder (None with --no-projects)."""
    if a.no_projects:
        return None
    return Path(a.projects) if a.projects else Path(a.bench).resolve().parents[1] / "projects"


def _save_projects(kind: str, a, **kw) -> None:
    """Save the run's Newtime chunks or the Newtone session as FL projects (best effort: a failure here never fails the run)."""
    d = _projects_dir(a)
    if d is None:
        return
    try:
        if kind == "chunks":
            done = sessionflp.chunk_projects(a.manifest, a.bench, str(d / "newtime"))
        else:
            done = [sessionflp.newtone_project(a.bench, str(d / "newtone"), kw["src"], kw["tuned"])]
        sessionflp.write_readme(str(d))
        print("saved %d FL projects under %s" % (len(done), d / ("newtime" if kind == "chunks" else "newtone")), flush=True)
    except Exception as e:  # noqa: BLE001
        print("could not save the projects: %s" % e, flush=True)


def cmd_bench(a) -> int:
    from coproducer import flpfile

    f = flpfile.Flp.load(a.src)
    f.set_tempo(a.bpm)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    f.save(a.out)
    print("bench at %g bpm: %s" % (a.bpm, a.out))
    return 0


def cmd_chunks(a) -> int:
    s = _session("vocal_chunks")
    if not _start_fl(s, Path(a.bench)):
        return 3
    opts = {"max_move_s": a.max_move, "min_share": a.min_share}
    if a.indices:
        opts["indices"] = [int(v) for v in a.indices.split(",")]
    try:
        r = s.registry.call("quantize_vocal_chunks_gui", manifest_path=a.manifest, lead_s=a.lead, passes=a.passes, target_ms=a.target_ms, options=opts)
        print("chunks", r.ok, json.dumps(r.value if r.ok else str(r.error), indent=1, default=str), flush=True)
        Path(a.manifest).with_name("fit_run.log.json").write_text(json.dumps(r.value if r.ok else {"error": str(r.error)}, indent=1, default=str), encoding="utf-8")
    finally:
        if not a.keep:
            _stop_fl()
    _save_projects("chunks", a)
    return 0 if r.ok else 1


def cmd_newtone(a) -> int:
    s = _session("vocal_newtone")
    if not _start_fl(s, Path(a.bench)):
        return 3
    try:
        kw = {"style": a.style}
        if a.midi:
            kw["midi_path"] = a.midi
        r = s.registry.call("apply_vocal_tuning_gui", path=a.src, out_path=a.out, **kw)
        print("newtone", r.ok, json.dumps(r.value if r.ok else str(r.error), indent=1, default=str), flush=True)
        Path(a.out).with_suffix(".newtone.log.json").write_text(json.dumps(r.value if r.ok else {"error": str(r.error)}, indent=1, default=str), encoding="utf-8")
    finally:
        if not a.keep:
            _stop_fl()
    if r.ok:
        _save_projects("newtone", a, src=a.src, tuned=a.out)
    return 0 if r.ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("bench")
    b.add_argument("--from", dest="src", required=True)
    b.add_argument("--out", required=True)
    b.add_argument("--bpm", type=float, required=True)
    c = sub.add_parser("chunks")
    c.add_argument("--manifest", required=True)
    c.add_argument("--bench", required=True)
    c.add_argument("--lead", type=float, default=-1.0)
    c.add_argument("--passes", type=int, default=2)
    c.add_argument("--target-ms", type=float, default=10.0)
    c.add_argument("--max-move", type=float, default=0.1)
    c.add_argument("--min-share", type=float, default=0.7)
    c.add_argument("--indices", default="")
    c.add_argument("--keep", action="store_true")
    c.add_argument("--projects", default="", help="folder for the saved FL projects (default: the song's projects folder)")
    c.add_argument("--no-projects", action="store_true")
    n = sub.add_parser("newtone")
    n.add_argument("--in", dest="src", required=True)
    n.add_argument("--out", required=True)
    n.add_argument("--bench", required=True)
    n.add_argument("--style", default="middle")
    n.add_argument("--midi", default="")
    n.add_argument("--keep", action="store_true")
    n.add_argument("--projects", default="")
    n.add_argument("--no-projects", action="store_true")
    a = ap.parse_args()
    if any("sandbox" not in Path(p).resolve().parts for p in [getattr(a, "out", None), getattr(a, "manifest", None)] if p):
        print("outputs must sit under a folder named sandbox", file=sys.stderr)
        return 2
    return {"bench": cmd_bench, "chunks": cmd_chunks, "newtone": cmd_newtone}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
