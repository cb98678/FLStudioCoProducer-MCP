"""Read a whole FL project from its file: channels (with Layer children), mixer inserts (names, routing, effect slots, levels), automation clips
and controller links resolved to names, arrangements with markers and named rows. Read only.

Format notes it relies on (FL 26.1.7 saves; see docs/FLP_FORMAT.md and docs/REFERENCE_FUTURE_HOUSE.md):
- An insert's name, colour and appearance flag come just before its flags event 236; its effect slots and routing event 235 follow it. Event 235 holds
  one byte per destination insert (0 is the master) and FL 26 trims the trailing zeros, so it can be 1 or 3 bytes long.
- A slot's plugin is event 201 (internal name), 212 (wrapper: insert u32, slot u32), optional 203 (name the person gave), 213 (state), then event 98.
- Mixer levels are records in event 225: id byte at 4, group byte at 5, insert << 6 | slot at 6, value at 8. The insert field of the master is 448 in
  FL 26 saves and 128 in FL 20 saves, so the base is read from the file. Group 32 records are send levels (the id byte is the destination insert); FL
  writes them only for sends away from the default, for example the level-0 sends to inserts 100 to 103 that FL 26 adds to most inserts.
- Event 227 links a source to a parameter: u16 output (0x8000 set for a controller output), u16 source (an automation clip or controller channel id,
  or a mixer plugin), u32, u32 target. A mixer target is 0x70000000 | insert << 22 | slot << 16 | param (param 0x8000 + k is plugin parameter k);
  a channel target is channel << 16 | param (param 0x8000 + k is the generator's parameter k).
"""
from __future__ import annotations

import struct
from collections import Counter

from . import flpfile
from .automation import decode_points, fader_to_db
from .flpfile import Flp, dec16

TYPES = {0: "sampler", 2: "plugin", 3: "layer", 4: "audio clip", 5: "automation"}
CHANNEL_PARAMS = {0: "volume", 1: "pan", 2: "filter cutoff", 3: "filter resonance", 4: "pitch"}
MIXER_PARAMS = {0x1FC0: "volume", 0x1FC1: "pan", 0x1FC2: "stereo separation"}
CONTROLLERS = ("Fruity Envelope Controller", "Fruity Keyboard Controller", "Fruity Formula Controller", "MIDI Out", "Fruity X-Y Controller")
METERS = ("Edison", "Wave Candy", "Fruity dB Meter", "Fruity Spectroman")


def _txt(v: bytes) -> str:
    try:
        return dec16(v)
    except UnicodeDecodeError:
        return ""


def project_info(f: Flp) -> dict:
    out: dict = {"ppq": struct.unpack("<H", f.head[12:14])[0]}
    keys = {194: "title", 207: "artists", 206: "genre", 195: "comments", 197: "url"}
    for e, v in f.events:
        if e in keys and keys[e] not in out:
            out[keys[e]] = _txt(v)
        elif e == 199 and "fl_version" not in out:
            raw = bytes(v)
            text = raw.decode("utf-16-le", "replace") if len(raw) > 1 and raw[1] == 0 else raw.decode("ascii", "replace")
            out["fl_version"] = text.rstrip("\x00")
    try:
        out["tempo"] = f.tempo()
    except flpfile.FlpError:
        out["tempo"] = None
    head = out.get("fl_version", "0").split(".")[0]
    major = int(head) if head.isdigit() else 0
    out["supported"] = major >= 21
    return out


def channels(f: Flp) -> list[dict]:
    groups = [_txt(v) for e, v in f.events if e == 231]
    uses = Counter(n[1] for ns in f.pattern_notes().values() for n in ns)
    out = []
    for ch in f.channel_ids():
        a, b = f.block(ch)
        d: dict = {"id": ch, "name": None, "type": None, "plugin": None, "insert": None, "group": None, "children": [], "pitch_cents": 0,
                   "pitch_range": 2, "sample": None, "notes": uses.get(ch, 0)}
        for e, v in f.events[a:b]:
            v = bytes(v)
            if e == 21 and d["type"] is None:
                d["type"] = TYPES.get(v[0], v[0])
            elif e == 201 and d["plugin"] is None:
                d["plugin"] = _txt(v) or None
            elif e == 203 and d["name"] is None:
                d["name"] = _txt(v)
            elif e == 196:
                d["sample"] = _txt(v).replace("/", "\\").split("\\")[-1]
            elif e == 104 and len(v) == 2:
                d["insert"] = struct.unpack("<H", v)[0]
            elif e == 145 and len(v) == 4:
                g = struct.unpack("<i", v)[0]
                d["group"] = groups[g] if 0 <= g < len(groups) else None
            elif e == 94 and len(v) == 2:
                d["children"].append(struct.unpack("<H", v)[0])
            elif e == 219 and len(v) >= 12:
                d["pitch_cents"] = struct.unpack_from("<i", v, 8)[0]
            elif e == 215 and len(v) >= 116:
                d["pitch_range"] = struct.unpack_from("<i", v, 112)[0]
        out.append(d)
    return out


def _mixer_records(f: Flp) -> dict[int, dict]:
    """{insert: {"volume_db", "pan", "slots": {slot: {"on", "mix"}}}} from event 225, with the insert base taken from the first volume record."""
    data = next((bytes(v) for e, v in f.events if e == 225), b"")
    recs = [struct.unpack("<IBBHi", data[k : k + 12]) for k in range(0, len(data) - 11, 12)]
    vols = [r[3] >> 6 for r in recs if r[1] == 192]
    base = min(vols) if vols else 0
    out: dict[int, dict] = {}
    for _a, pid, group, cd, val in recs:
        t = out.setdefault((cd >> 6) - base, {"slots": {}, "sends": {}})
        if group == 32:  # a send level record: pid is the destination insert (FL stores only sends that are not at the default)
            t["sends"][pid] = round(val / 16000.0, 3)
        elif pid == 192:
            t["volume_db"] = round(fader_to_db(val / 16000.0), 1)
        elif pid == 193:
            t["pan"] = val
        elif pid in (0, 1):
            t["slots"].setdefault(cd & 0x3F, {})["on" if pid == 0 else "mix"] = val
    return out


def inserts(f: Flp) -> list[dict]:
    ev = f.events
    marks = [i for i, (e, _v) in enumerate(ev) if e == 236]
    levels = _mixer_records(f)
    out, prev = [], 0
    for n, at in enumerate(marks):
        end = marks[n + 1] if n + 1 < len(marks) else len(ev)
        row: dict = {"index": n, "name": None, "rgb": None, "routes": [], "slots": []}
        for e, v in ev[prev:at]:
            if e == 204:
                row["name"] = _txt(v)
            elif e == 149 and len(v) == 4:
                row["rgb"] = tuple(bytes(v)[:3])
        row.update(_insert_body(ev[at + 1 : end]))
        lv = levels.get(n, {})
        row["volume_db"] = lv.get("volume_db")
        sends = lv.get("sends", {})
        row["routes"] = [{"to": d, "level": sends.get(d)} for d in row["routes"]]
        for s in row["slots"]:
            st = lv.get("slots", {}).get(s["slot"], {})
            s["mix"] = round(st["mix"] / 12800.0, 3) if "mix" in st else None
        out.append(row)
        prev = at
    return out


def _insert_body(body: list) -> dict:
    slots, cur, routes = [], None, []
    for e, v in body:
        v = bytes(v)
        if e == 201:
            cur = {"plugin": _txt(v), "slot": None, "user_name": None}
        elif e == 212 and cur is not None and len(v) >= 8:
            cur["slot"] = struct.unpack_from("<I", v, 4)[0]
        elif e == 203 and cur is not None:
            cur["user_name"] = _txt(v)
        elif e == 213 and cur is not None:
            slots.append(cur)
            cur = None
        elif e == 235:
            routes = [k for k, b in enumerate(v) if b == 1]
    return {"slots": slots, "routes": routes}


def links(f: Flp) -> list[dict]:
    out = []
    for e, v in f.events:
        if e == 227 and len(v) == 20:
            outp, src, _x, target, _y, _z = struct.unpack("<HHIIII", bytes(v))
            out.append({"output": outp & 0x7FFF, "controller": bool(outp & 0x8000), "source": src, "target": target})
    return out


def describe_target(target: int, ins: list[dict], chans: dict[int, dict]) -> dict:
    """What a link target points at, with names where the file has them."""
    if target >> 28 == 0x7:
        track, slot, param = (target - 0x70000000) >> 22, (target >> 16) & 0x3F, target & 0xFFFF
        name = ins[track]["name"] if track < len(ins) else None
        if param >= 0x8000:
            plug = next((s["plugin"] for s in (ins[track]["slots"] if track < len(ins) else []) if s["slot"] == slot), None)
            return {"kind": "plugin", "insert": track, "insert_name": name or ("Master" if track == 0 else None), "slot": slot, "plugin": plug,
                    "param": param - 0x8000}
        return {"kind": "mixer", "insert": track, "insert_name": name, "slot": slot, "param": MIXER_PARAMS.get(param, hex(param))}
    if target >> 31:  # a plugin addressed by a global reference (seen for a Control Surface on insert 100: 0x8900); not decoded further
        return {"kind": "mixer plugin", "ref": "%#x" % (target >> 16), "param": (target & 0xFFFF) - 0x8000 if target & 0x8000 else target & 0xFFFF}
    ch, param = target >> 16, target & 0xFFFF
    c = chans.get(ch, {})
    if param >= 0x8000:
        return {"kind": "generator", "channel": ch, "channel_name": c.get("name"), "plugin": c.get("plugin"), "param": param - 0x8000}
    return {"kind": "channel", "channel": ch, "channel_name": c.get("name"), "param": CHANNEL_PARAMS.get(param, param)}


def automation(f: Flp, ins: list[dict], chans: list[dict]) -> dict:
    by_id = {c["id"]: c for c in chans}
    clips, controllers = [], []
    clip_ids = {c["id"] for c in chans if c["type"] == "automation"}
    lk = links(f)
    for c in chans:
        if c["type"] != "automation":
            continue
        a, b = f.block(c["id"])
        pts = next((bytes(v) for e, v in f.events[a:b] if e == 234), b"")
        points = decode_points(pts) if pts else []
        targets = [describe_target(x["target"], ins, by_id) for x in lk if x["source"] == c["id"] and not x["controller"]]
        clips.append({"channel": c["id"], "name": c["name"], "targets": targets, "points": len(points),
                      "beats": round(points[-1][0], 2) if points else 0, "range": [round(min(p[1] for p in points), 3), round(max(p[1] for p in points), 3)] if points else None})
    for x in lk:
        if x["controller"] or (x["source"] not in clip_ids and x["source"] in by_id):
            src = by_id.get(x["source"], {"name": "mixer plugin %#x" % x["source"] if x["source"] >= 0x8000 else None})
            controllers.append({"source": x["source"], "source_name": src.get("name"), "source_plugin": src.get("plugin"), "output": x["output"],
                                "target": describe_target(x["target"], ins, by_id)})
    return {"clips": clips, "controllers": controllers, "orphans": [c["name"] for c in clips if not c["targets"]]}


def arrangement_list(f: Flp) -> list[dict]:
    cur = f.current_arrangement()
    out = []
    for a in f.arrangements():
        rows, last = {}, None
        for i in range(a["start"], a["end"]):
            e, v = f.events[i]
            if e == 238 and len(v) >= 4:
                last = struct.unpack("<I", bytes(v)[:4])[0]
            elif e == 239 and last is not None:
                rows[last] = _txt(v)
        items = bytes(f.events[a["playlist"]][1]) if a["playlist"] is not None else b""
        size = f.playlist_item_size(len(items))               # 32, 60, 80 or 88 bytes by the FL version that saved the file
        n = len(items) // size
        ends = [struct.unpack_from("<I", items, k)[0] + struct.unpack_from("<I", items, k + 8)[0] for k in range(0, n * size, size)]
        markers = _markers(f, a)
        bar = f.ppq * 4                                        # ticks per 4/4 bar: most projects use PPQ 96, some older ones 72 or 192
        out.append({"id": a["id"], "name": a["name"], "current": cur is not None and a["id"] == cur["id"], "clips": n, "named_rows": rows,
                    "bars": round(max(ends) / bar, 2) if ends else 0, "markers": markers})
    return out


def _markers(f: Flp, a: dict) -> list[dict]:
    out = []
    for i in range(a["start"], a["end"]):
        e, v = f.events[i]
        if e == flpfile.EV_MARKER_POS and len(v) == 4:
            out.append({"bar": round((struct.unpack("<I", bytes(v))[0] & 0x07FFFFFF) / (f.ppq * 4) + 1, 2), "name": None})
        elif e == flpfile.EV_MARKER_NAME and out and out[-1]["name"] is None:
            out[-1]["name"] = _txt(v)
    return out


def summary(rep: dict) -> list[str]:
    """Plain lines an agent or a person can read first."""
    ins = [i for i in rep["inserts"] if i["slots"] or i["name"]]
    lines = ["%s, %s BPM, FL %s" % (rep["project"].get("title") or "untitled", rep["project"].get("tempo"), rep["project"].get("fl_version"))]
    feeds: dict[int, list[int]] = {}
    for i in ins:
        for r in i["routes"]:
            if r["to"] != 0 and r["level"] != 0:
                feeds.setdefault(r["to"], []).append(i["index"])
    for bus, srcs in sorted(feeds.items()):
        lines.append("bus %d %s takes inserts %s" % (bus, rep["inserts"][bus]["name"], srcs))
    for c in rep["channels"]:
        if c["type"] == "layer" and c["children"]:
            lines.append("layer %s triggers channels %s" % (c["name"], c["children"]))
    pump = Counter((x["source_name"], x["target"].get("plugin"), x["target"].get("param")) for x in rep["automation"]["controllers"])
    for (src, plug, param), n in pump.items():
        lines.append("controller %s drives %s param %s on %d insert(s)" % (src, plug, param, n))
    lines.append("%d automation clips, orphans: %s" % (len(rep["automation"]["clips"]), rep["automation"]["orphans"] or "none"))
    cur = next((a for a in rep["arrangements"] if a["current"]), None)
    if cur:
        lines.append("current arrangement %r, %s bars, markers %s" % (cur["name"], cur["bars"], [(m["bar"], m["name"]) for m in cur["markers"]]))
    return lines


def read(f: Flp) -> dict:
    chans = channels(f)
    ins = inserts(f)
    placed = sorted({struct.unpack_from("<H", it, 6)[0] for it in f.playlist_items()}) if f.current_arrangement() else []
    rep = {"project": project_info(f), "channels": chans, "inserts": ins, "automation": automation(f, ins, chans),
           "arrangements": arrangement_list(f), "groups": [_txt(v) for e, v in f.events if e == 231], "placed_channels": placed}
    rep["summary"] = summary(rep)
    return rep


def _db(text) -> float | None:
    """'4.0dB' or '-0.2 dB' as a float; None when the text is not a level."""
    import re

    m = re.match(r"\s*([-+]?\d+(?:\.\d+)?)\s*dB", str(text or ""))
    return float(m.group(1)) if m else None


def _master_issues(params: dict | None) -> list[dict]:
    """With a live parameter snapshot (snapshot_project_params), flag a master whose last limiter lets the output pass 0 dBFS."""
    if not params:
        return [{"kind": "master_unchecked", "severity": "info", "detail": "limiter ceiling not checked: pass a live parameter snapshot to check it"}]
    master = next((i for i in params.get("inserts", []) if i.get("index") == 0), None)
    out = []
    for s in (master or {}).get("slots", []):
        by = {p["name"]: p.get("text") for p in s.get("params", {}).values()}
        ceiling = _db(by.get("Limiter ceiling")) if s.get("plugin") == "Fruity Limiter" else _db(by.get("Master soft saturation ceiling")) if s.get("plugin") == "Maximus" else None
        if ceiling is not None and ceiling > 0:
            out.append({"kind": "master_over_zero", "severity": "problem", "detail": "%s in master slot %d has its ceiling at %+.1f dB, so the output can pass 0 dBFS" % (s["plugin"], s["slot"], ceiling)})
    return out


def health(rep: dict, params: dict | None = None, not_owned: list | None = None) -> list[dict]:
    """Problems a producer would want fixed before mixing or rendering, from an anatomy report (and optionally a live parameter snapshot)."""
    out = [] if rep["project"].get("supported", True) else [{"kind": "old_format", "severity": "problem", "detail": "saved by FL %s: re-save in FL 26 before editing" % rep["project"].get("fl_version")}]
    out += [{"kind": "orphan_automation", "severity": "problem", "detail": "automation clip %r is linked to nothing" % n} for n in rep["automation"]["orphans"]]
    placed = set(rep.get("placed_channels", []))
    out += [{"kind": "unplaced_automation", "severity": "info", "detail": "automation clip %r is not in the playlist" % c["name"]} for c in rep["automation"]["clips"] if placed and c["channel"] not in placed]
    for i in rep["inserts"]:
        for s in i["slots"]:
            if s["plugin"] in METERS:
                out.append({"kind": "meter_in_chain", "severity": "info", "detail": "%s in insert %d (%s) slot %d" % (s["plugin"], i["index"], i["name"], s["slot"])})
            if not_owned and s["plugin"] in not_owned:
                out.append({"kind": "not_owned", "severity": "problem", "detail": "%s in insert %d slot %d is not in this FL edition: FL shows a trial dialog and command-line renders stall" % (s["plugin"], i["index"], s["slot"])})
    for c in rep["channels"]:
        if not c["name"] and c["type"] != "automation":
            out.append({"kind": "unnamed_channel", "severity": "info", "detail": "channel %d (%s%s) has no name" % (c["id"], c["type"], ", " + c["plugin"] if c["plugin"] else "")})
        if not_owned and c["plugin"] in not_owned:
            out.append({"kind": "not_owned", "severity": "problem", "detail": "channel %d uses %s, not in this FL edition" % (c["id"], c["plugin"])})
    targets = {c["insert"] for c in rep["channels"] if c["insert"]} | {r["to"] for i in rep["inserts"] for r in i["routes"] if r["level"] != 0}
    out += [{"kind": "empty_insert", "severity": "info", "detail": "insert %d %r has no effects and nothing routed to it" % (i["index"], i["name"])}
            for i in rep["inserts"] if i["name"] and not i["slots"] and i["index"] not in targets]
    extra = [a["name"] for a in rep["arrangements"] if not a["current"]]
    if extra:
        out.append({"kind": "extra_arrangements", "severity": "info", "detail": "arrangements besides the current one: %s" % extra})
    return out + _master_issues(params)
