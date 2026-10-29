"""Effect library: copy effect settings out of an FL-saved project, list them, and put one into an empty mixer slot of a sandbox copy.

    python tools/fx_library.py extract PROJECT.flp --insert 1 --slot 2 --name "Vocal Chop Reverb" [--params live.json] [--notes TEXT]
    python tools/fx_library.py extract-all PROJECT.flp --prefix fh --params live.json [--skip "Transient Processor,Edison"]
    python tools/fx_library.py extract-channel PROJECT.flp --channel 30 --name "fh noise riser" [--params live.json] [--notes TEXT]
    python tools/fx_library.py list
    python tools/fx_library.py inject IN.flp OUT.flp --insert 9 --slot 0 --name "fh vocal chop reverb"

--params is a JSON snapshot from tools/dump_project_live.py; its parameter texts are stored with the entry so a later live read can confirm the
injection. OUT must sit under a folder named sandbox; IN is never written. Entries live in plugins/library/.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from coproducer import anatomy, flpfile, fxlib  # noqa: E402


def _live_params(path: str, insert: int, slot: int) -> dict:
    if not path:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    ins = next((i for i in data.get("inserts", []) if i.get("index") == insert), {})
    s = next((x for x in ins.get("slots", []) if x.get("slot") == slot), {})
    return {p["name"]: p.get("text") for p in s.get("params", {}).values()}


def _channel_params(path: str, channel: int) -> dict:
    if not path:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    c = next((x for x in data.get("channels", []) if x.get("index") == channel), {})
    return {p["name"]: p.get("text") for p in c.get("params", {}).values()}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=("extract", "extract-all", "extract-channel", "list", "inject"))
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--insert", type=int, default=-1)
    ap.add_argument("--slot", type=int, default=-1)
    ap.add_argument("--channel", type=int, default=-1)
    ap.add_argument("--name", default="")
    ap.add_argument("--params", default="")
    ap.add_argument("--notes", default="")
    ap.add_argument("--prefix", default="")
    ap.add_argument("--skip", default="")
    a = ap.parse_args()
    if a.mode == "list":
        for e in fxlib.list_entries():
            print("%-48s %-28s %s" % (e["name"], e["plugin"], e["notes"]))
        return 0
    if a.mode == "inject":
        src, out = a.paths
        if "sandbox" not in [p.lower() for p in Path(out).resolve().parts]:
            sys.exit("refusing %s: output must be under a folder named sandbox" % out)
        f = flpfile.Flp.load(src)
        fxlib.inject(f, a.insert, a.slot, fxlib.load_entry(a.name))
        f.save(out)
        print("wrote", out, "with", a.name, "in insert", a.insert, "slot", a.slot)
        return 0
    f = flpfile.Flp.load(a.paths[0])
    source = Path(a.paths[0]).name
    if a.mode == "extract-channel":
        e = fxlib.extract_channel(f, a.channel, a.name, source, _channel_params(a.params, a.channel), a.notes)
        print("saved", fxlib.save_entry(e))
        return 0
    if a.mode == "extract":
        e = fxlib.extract(f, a.insert, a.slot, a.name, source, _live_params(a.params, a.insert, a.slot), a.notes)
        print("saved", fxlib.save_entry(e))
        return 0
    skip = {x.strip() for x in a.skip.split(",") if x.strip()}
    for ins in anatomy.inserts(f):
        for s in ins["slots"]:
            if s["plugin"] in skip:
                continue
            label = "%s %s %s" % (a.prefix, ins["name"] or ("master" if ins["index"] == 0 else "insert %d" % ins["index"]), s["plugin"])
            if any(x["plugin"] == s["plugin"] for x in ins["slots"] if x["slot"] < s["slot"]):
                label += " %d" % s["slot"]
            e = fxlib.extract(f, ins["index"], s["slot"], label, source, _live_params(a.params, ins["index"], s["slot"]), "from %s insert %d slot %d" % (source, ins["index"], s["slot"]))
            print("saved", fxlib.save_entry(e))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
