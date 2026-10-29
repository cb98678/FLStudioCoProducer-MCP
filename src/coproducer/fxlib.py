"""A library of effect settings copied from projects FL saved, and putting them into an empty mixer slot of another FL-saved project.

An effect in a mixer slot is a run of events in the insert's block: 201 (internal name), 212 (wrapper: insert u32, slot u32, then 44 bytes), an
optional 203 (the name the person gave), 155, 128, 41 and 213 (the plugin's own state), followed by event 98 with the slot index. An empty slot is
only its event 98. Copying the run, with the wrapper's insert and slot rewritten, moves the effect with all its settings, including ones FL's API
does not expose (an Envelope Controller's drawn envelope, Soundgoodizer's mode). The person approved copying settings from the FL demo
"Future House" into this library (2026-10-25). Only inject into a project FL itself saved (see docs/FLP_FORMAT.md, "Only inject into a project FL
itself saved"), then check in FL that the parameters read back as the entry says.
"""
from __future__ import annotations

import json
import re
import struct
from pathlib import Path

from .flpfile import Flp, FlpError, dec16

LIBRARY = Path(__file__).resolve().parents[2] / "plugins" / "library"
SLOT_END = 98


def _insert_body(f: Flp, insert: int) -> tuple[int, int]:
    """Event range of an insert's slots: from just after its flags event 236 to its routing event 235."""
    marks = [i for i, (e, _v) in enumerate(f.events) if e == 236]
    if insert >= len(marks):
        raise FlpError("insert %d not in the file (it has %d)" % (insert, len(marks)))
    a = marks[insert] + 1
    b = next(i for i in range(a, len(f.events)) if f.events[i][0] in (235, 236))
    return a, b


def _slot_ends(f: Flp, insert: int) -> dict[int, int]:
    a, b = _insert_body(f, insert)
    return {struct.unpack("<H", bytes(f.events[i][1])[:2])[0]: i for i in range(a, b) if f.events[i][0] == SLOT_END}


def _run(f: Flp, insert: int, slot: int) -> tuple[int, int] | None:
    """Event range [start, end) of the effect in a slot (end is its event 98), or None when the slot is empty."""
    ends = _slot_ends(f, insert)
    if slot not in ends:
        raise FlpError("insert %d has no slot %d marker" % (insert, slot))
    end = ends[slot]
    start = end
    while start - 1 >= 0 and f.events[start - 1][0] not in (SLOT_END, 236):
        start -= 1
    return (start, end) if start < end and f.events[start][0] == 201 else None


def slot_plugin(f: Flp, insert: int, slot: int) -> str | None:
    r = _run(f, insert, slot)
    return dec16(f.events[r[0]][1]) if r else None


def slot_name(f: Flp, insert: int, slot: int) -> str | None:
    """The name the slot was given (event 203 in its run), or None."""
    r = _run(f, insert, slot)
    return next((dec16(v) for e, v in f.events[r[0] : r[1]] if e == 203), None) if r else None


def set_slot_name(f: Flp, insert: int, slot: int, name: str) -> None:
    """Name an effect slot (FL shows it in the mixer), so a recipe can find the instance it placed."""
    from .flpfile import enc16

    r = _run(f, insert, slot)
    if not r:
        raise FlpError("insert %d slot %d is empty" % (insert, slot))
    for k in range(r[0], r[1]):
        if f.events[k][0] == 203:
            f.events[k][1] = enc16(name)
            return
    at = next(k for k in range(r[0], r[1]) if f.events[k][0] == 212) + 1
    f.events.insert(at, [203, enc16(name)])


def find_named_slot(f: Flp, insert: int, name: str) -> int | None:
    return next((s for s in range(10) if slot_name(f, insert, s) == name), None)


def extract(f: Flp, insert: int, slot: int, name: str, source: str = "", params: dict | None = None, notes: str = "") -> dict:
    """A library entry for the effect in (insert, slot): its events as hex, plus the parameter texts read live when given."""
    r = _run(f, insert, slot)
    if not r:
        raise FlpError("insert %d slot %d is empty" % (insert, slot))
    events = [[e, bytes(v).hex()] for e, v in f.events[r[0] : r[1]]]
    return {"name": name, "plugin": dec16(f.events[r[0]][1]), "source": source, "from": {"insert": insert, "slot": slot},
            "notes": notes, "params": params or {}, "events": events}


def inject(f: Flp, insert: int, slot: int, entry: dict) -> None:
    """Put a library entry's effect into an empty slot. Refuses a taken slot. Switches the slot on in the mixer records when they exist."""
    if _run(f, insert, slot):
        raise FlpError("insert %d slot %d already holds %s" % (insert, slot, slot_plugin(f, insert, slot)))
    end = _slot_ends(f, insert)[slot]
    events = []
    for e, h in entry["events"]:
        v = bytes.fromhex(h)
        if e == 212 and len(v) >= 8:
            v = struct.pack("<II", insert, slot) + v[8:]
        events.append([e, v])
    if not events or events[0][0] != 201:
        raise FlpError("library entry %r does not start with a plugin name event" % entry.get("name"))
    f.events[end:end] = events
    try:
        f.set_slot_enabled(insert, slot, True)
    except FlpError:
        pass


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def save_entry(entry: dict, folder: Path | str = LIBRARY) -> Path:
    p = Path(folder) / (slug(entry["name"]) + ".json")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(entry, indent=1), encoding="utf-8")
    return p


def load_entry(name: str, folder: Path | str = LIBRARY) -> dict:
    p = Path(folder) / (slug(name) + ".json")
    if not p.is_file():
        raise FlpError("no library entry %r in %s" % (name, folder))
    return json.loads(p.read_text(encoding="utf-8"))


def list_entries(folder: Path | str = LIBRARY) -> list[dict]:
    out = []
    for p in sorted(Path(folder).glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        out.append({"name": d["name"], "kind": d.get("kind", "effect"), "plugin": d["plugin"], "notes": d.get("notes", ""), "source": d.get("source", "")})
    return out


# ---- channel entries (a generator or controller channel with its state, e.g. the Envelope Controller that drives a pump)
def extract_channel(f: Flp, ch: int, name: str, source: str = "", params: dict | None = None, notes: str = "") -> dict:
    a, b = f.block(ch)
    events = [[e, bytes(v).hex()] for e, v in f.events[a:b]]
    plug = next((dec16(v) for e, v in f.events[a:b] if e == 201), "")
    return {"name": name, "kind": "channel", "plugin": plug, "source": source, "from": {"channel": ch}, "notes": notes, "params": params or {}, "events": events}


def add_channel(f: Flp, entry: dict, new_id: int, name: str, track: int = 0) -> None:
    """Add a channel entry as a new channel (after the last channel), with its own id, name and mixer track."""
    if entry.get("kind") != "channel":
        raise FlpError("library entry %r is not a channel" % entry.get("name"))
    if new_id in f.channel_ids():
        raise FlpError("channel id %d already exists" % new_id)
    from .flpfile import EV_CH_NAME, EV_CH_TRACK, enc16

    block = [[e, bytes.fromhex(h)] for e, h in entry["events"]]
    block[0][1] = struct.pack("<H", new_id)
    for x in block:
        if x[0] == EV_CH_NAME:
            x[1] = enc16(name)
        elif x[0] == EV_CH_TRACK and len(x[1]) == 2:
            x[1] = struct.pack("<H", track)
    _, end = f.block(f.channel_ids()[-1])
    f.events[end:end] = block
    f._set_channel_count(f.channel_count + 1)
