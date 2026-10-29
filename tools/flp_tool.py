"""Offline editable-first patching of a sandbox copy of an FL Studio 2026 project. Run from the repo root.

    python tools/flp_tool.py info P.flp
    python tools/flp_tool.py kit OUT_DIR
    python tools/flp_tool.py set-sample IN.flp OUT.flp CH WAV [--name NAME]
    python tools/flp_tool.py enable IN.flp OUT.flp CH on|off
    python tools/flp_tool.py clone IN.flp OUT.flp SRC_CH NEW_CH NAME [--track N]
    python tools/flp_tool.py add-drums IN.flp OUT.flp PLAN.json [--strip] [--track 43] [--base-id 30]
    python tools/flp_tool.py add-notes IN.flp OUT.flp NOTES.json [--track 44] [--base-id 100]

PLAN.json: {"sections": [{"name","start","end"}], "fills": {"7": "A"}, "crashes": {"8": 0.75} or "default",
            "channels": {"kick": 2, "snare": 3, ...}}
NOTES.json: {"channel": 160, "label": "SUB", "notes": [[start_beat, dur_beats, key, vel], ...]}
The output path must sit under a folder named sandbox (or pass --force). The input is never written.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from coproducer import drumplan, flpfile  # noqa: E402


def _guard(out: str, force: bool) -> None:
    if not force and "sandbox" not in [p.lower() for p in Path(out).resolve().parts]:
        sys.exit("refusing to write %s: output must be under a folder named sandbox (or pass --force)" % out)


def cmd_info(a: argparse.Namespace) -> None:
    f = flpfile.Flp.load(a.flp)
    print("channels (header %d, found %d), patterns %d, playlist items %d" % (f.channel_count, len(f.channel_ids()), len(f.pattern_ids()), len(f.playlist_items())))
    for ch in f.channel_ids():
        try:
            name = f.get_text(ch, flpfile.EV_CH_NAME)
        except flpfile.FlpError:
            name = ""
        try:
            path = f.get_text(ch, flpfile.EV_SAMPLE_PATH)
        except flpfile.FlpError:
            path = ""
        print("%4d  %-28s %s" % (ch, name, path))


def cmd_kit(a: argparse.Namespace) -> None:
    from coproducer import oneshots

    for name, p in oneshots.write_kit(a.out_dir).items():
        print(name, p)


def _edit(a: argparse.Namespace, fn) -> None:
    _guard(a.out, a.force)
    f = flpfile.Flp.load(a.flp)
    fn(f)
    f.save(a.out)
    print("wrote", a.out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name: str, *args: str) -> argparse.ArgumentParser:
        p = sub.add_parser(name)
        for x in args:
            p.add_argument(x)
        return p

    add("info", "flp")
    add("kit", "out_dir")
    for name, extra in (("set-sample", ("ch", "wav")), ("enable", ("ch", "state")), ("clone", ("src", "new", "name")),
                        ("add-drums", ("plan",)), ("add-notes", ("notes",))):
        p = add(name, "flp", "out", *extra)
        p.add_argument("--force", action="store_true")
        p.add_argument("--name")
        p.add_argument("--track", type=int)
        p.add_argument("--base-id", type=int)
        p.add_argument("--strip", action="store_true")
    a = ap.parse_args()
    if a.cmd == "info":
        cmd_info(a)
    elif a.cmd == "kit":
        cmd_kit(a)
    elif a.cmd == "set-sample":
        _edit(a, lambda f: f.set_sample(int(a.ch), a.wav, a.name))
    elif a.cmd == "enable":
        _edit(a, lambda f: f.set_enabled(int(a.ch), a.state == "on"))
    elif a.cmd == "clone":
        _edit(a, lambda f: f.clone_channel(int(a.src), int(a.new), a.name, a.track))
    elif a.cmd == "add-drums":
        plan = json.loads(Path(a.plan).read_text(encoding="utf-8"))
        secs = plan["sections"]
        crashes = drumplan.default_crashes(secs) if plan.get("crashes") == "default" else {int(k): v for k, v in plan.get("crashes", {}).items()}
        pl = drumplan.plan_drums(secs, {int(k): v for k, v in plan.get("fills", {}).items()}, crashes)
        chans = plan["channels"]

        def go(f: flpfile.Flp) -> None:
            if a.strip:
                print("removed old notes:", f.strip_notes(set(chans.values())))
            base = a.base_id or f.next_pattern_id(30)
            m = f.add_part("DR", drumplan.to_note_bytes(pl, chans), a.track or 43, base)
            print("patterns", len(set(m.values())), "bars", len(m))

        _edit(a, go)
    elif a.cmd == "add-notes":
        spec = json.loads(Path(a.notes).read_text(encoding="utf-8"))

        def go2(f: flpfile.Flp) -> None:
            base = a.base_id or f.next_pattern_id(100)
            m = f.add_part(spec.get("label", "PART"), flpfile.notes_by_bar([tuple(n) for n in spec["notes"]], spec["channel"]), a.track or 44, base)
            print("patterns", len(set(m.values())), "bars", len(m))

        _edit(a, go2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
