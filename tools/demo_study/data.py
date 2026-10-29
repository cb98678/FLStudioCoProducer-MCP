"""Study data per demo project (JSON), for docs/demo_study: meta, sections, harmony, drum grooves per channel, parts with plugin, FLEX preset,
insert chain, register and presence, the most common bar of each melodic part, mixer buses and sends, automation targets, controllers,
muted clips and bounces, the master pitch, the render's audio key, and the drum kit's sample paths. Comments and NoteBook text are not
copied (they hold lyrics). python tools/demo_study/data.py [--flp-dir sandbox/demo_study/flp]"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from coproducer import anatomy, flpfile, projmusic  # noqa: E402

ARGS = dict(zip(sys.argv[1::2], sys.argv[2::2]))
SRC = Path(ARGS.get("--flp-dir", ROOT / "sandbox" / "demo_study" / "flp"))
OUT = ROOT / "docs" / "demo_study" / "data"
OUT.mkdir(parents=True, exist_ok=True)
AK = Path(ARGS.get("--audio-keys", ROOT / "sandbox" / "demo_study" / "audio_keys.json"))   # tools/demo_study/keys.py
AUDIO_KEYS = json.loads(AK.read_text()) if AK.is_file() else {}   # the key of each full-mix render, from the audio (dsp.estimate_key)


def strs(b, n=5):
    return [x.group().decode() for x in re.finditer(rb"[ -~]{%d,}" % n, b or b"")]


def slug(stem):
    return re.sub(r"[^A-Za-z0-9]+", "_", stem.encode("ascii", "ignore").decode()).strip("_")[:60]


def factory(path):
    if not path:
        return None
    p = path.replace("/", "\\")
    p = re.sub(r"^%FLStudioData%", r"%FLStudioFactoryData%\\Data", p)
    return p


def data(p):
    f = flpfile.Flp.load(p)
    rep = anatomy.read(f)
    m = projmusic.read(f, rep)
    notes = projmusic.song_notes(f)
    for c in rep["channels"]:
        if c.get("type") == "layer" and notes.get(c["id"]):
            for kid in c.get("children") or []:
                notes[kid] = sorted(notes.get(kid, []) + [(n[0], kid, n[2], n[3], n[4]) for n in notes[c["id"]]])
    audio = projmusic.audio_regions(f)
    chans = {c["id"]: c for c in rep["channels"]}
    ins = {i["index"]: i for i in rep["inserts"]}
    pr = rep["project"]
    secs = m["sections"]
    d = {"file": p.name, "title": (pr.get("title") or "").strip(), "artists": (pr.get("artists") or "").strip(), "genre": (pr.get("genre") or "").strip(),
         "fl_version": pr.get("fl_version"), "ppq": f.ppq, "bpm": f.tempo(), "bars": m["bars"], "seconds": round(m["bars"] * 240.0 / f.tempo(), 1),
         "key": m["key"], "roles": dict(m["roles"]),
         "sections": [{"start_bar": s["start_bar"], "bars": s["bars"], "name": s.get("name") or s.get("kind") or "", "energy": s.get("energy"), "roles": s["roles"]} for s in secs],
         "progression": [{"chord": x["chord"], "roman": x["roman"], "bars": x["bars"]} for x in m["progression"]],
         "markers": [{"bar": round(mk["pos"] / (f.ppq * 4.0) + 1, 2), "name": mk["name"]} for mk in f.time_markers()]}
    drums = []
    kit = defaultdict(list)
    for pp in m["parts"]:
        if pp["role"] != "drums":
            continue
        ns = notes.get(pp["channel"]) or [(st, pp["channel"], 60, ln, 100) for st, ln in audio.get(pp["channel"], [])]
        if not ns:
            continue
        g = projmusic.groove(ns)
        v = projmusic.drum_voice(pp["name"] or "") or projmusic.drum_voice(pp["sample"] or "") or "perc"
        drums.append({"voice": v, "channel": pp["channel"], "name": pp["name"], "pattern": g["pattern"], "hits_per_bar": g["hits_per_bar"],
                      "late_16ths": g["late_16ths"], "velocity": g["velocity"], "bars": g["bars"]})
        smp = factory(f.channel_info(pp["channel"])["sample"])
        if smp:
            kit[v].append({"name": pp["name"], "sample": smp, "hits": len(ns)})
    d["drums"] = sorted(drums, key=lambda r: (r["voice"], -r["bars"]))
    d["kit"] = {v: sorted(rows, key=lambda r: -r["hits"])[:3] for v, rows in kit.items()}
    parts = []
    for pp in m["parts"]:
        c = chans[pp["channel"]]
        preset = None
        if c.get("plugin") == "FLEX":
            s = strs(f.plugin_state(pp["channel"]))
            preset = " / ".join(s[:2]) if s else None
        i = ins.get(c.get("insert")) if c.get("insert") is not None else None
        ns = notes.get(pp["channel"], [])
        row = {"channel": pp["channel"], "role": pp["role"], "name": pp["name"], "plugin": pp["plugin"], "sample": (pp["sample"] or "").rsplit("\\", 1)[-1] or None,
               "preset": preset, "insert": c.get("insert"), "insert_name": (i or {}).get("name"),
               "chain": [s["plugin"] for s in (i or {}).get("slots", [])], "range": [projmusic.note_name(x) for x in pp["range"]] if pp["range"] else None,
               "polyphony": pp["polyphony"], "median_len_beats": pp["median_len_beats"], "notes": pp["notes"], "clips": pp["clips"], "group": pp.get("group"),
               "presence": projmusic.presence(ns, audio.get(pp["channel"], []), secs)}
        if pp["role"] in ("bass", "chords", "pad", "lead", "arp", "vocal") and len(ns) >= 8:
            b = projmusic.busiest_bar(ns)
            row["bar"] = {"from_bar": b, "roll": projmusic.roll(ns, b, 2)}
        parts.append(row)
    d["parts"] = parts
    feeds = defaultdict(list)
    for i in rep["inserts"]:
        for r in i["routes"]:
            if r["to"] < 100 and r["to"] != 0:
                feeds[r["to"]].append(i["index"])
    d["mixer"] = [{"index": i["index"], "name": i.get("name") or ("Master" if i["index"] == 0 else ""), "volume_db": i.get("volume_db"),
                   "to": [r["to"] for r in i["routes"] if r["to"] < 100], "fed_by": feeds.get(i["index"], []),
                   "slots": [{"plugin": s["plugin"], "name": s.get("user_name")} for s in i["slots"]]}
                  for i in rep["inserts"] if i.get("slots") or i.get("name") or feeds.get(i["index"]) or i["index"] == 0]
    autos = []
    for a in rep["automation"]["clips"]:
        t = a["targets"][0] if a["targets"] else {}
        autos.append({"name": a["name"], "kind": t.get("kind"), "plugin": t.get("plugin"), "param": t.get("param"), "insert": t.get("insert_name"),
                      "channel": t.get("channel_name"), "points": a["points"], "beats": a["beats"], "range": a["range"]})
    d["automation"] = autos
    d["automation_summary"] = dict(Counter(((x["plugin"] or x["kind"] or "?") for x in autos)).most_common())
    d["controllers"] = rep["automation"].get("controllers") or []
    plug = Counter()
    for pp in parts:
        if pp["plugin"]:
            plug[pp["plugin"]] += 1
    d["plugins"] = dict(plug.most_common())
    d["effects"] = dict(Counter(s["plugin"] for i in rep["inserts"] for s in i["slots"]).most_common())
    # clips muted in the playlist play nothing; a part whose MIDI is all muted was usually bounced to audio (its notes are the bounce's score)
    items = f.playlist_items()
    d["muted_clips"] = sum(1 for it in items if f.item_muted(it))
    playing, every = projmusic.song_notes(f), projmusic.song_notes(f, muted=True)
    bounce = [c["name"] for c in rep["channels"] if re.search(r"render|resampl|bounce|print", c.get("name") or "", re.I)]
    d["muted_parts"] = [{"channel": ch, "name": chans[ch].get("name"), "muted_notes": len(ns) - len(playing.get(ch, [])), "playing_notes": len(playing.get(ch, []))}
                        for ch, ns in sorted(every.items()) if ch in chans and len(ns) - len(playing.get(ch, [])) >= 8]
    d["bounces"] = bounce
    for x in d["muted_parts"]:   # a part whose MIDI is all muted still has a patch worth studying: list it, marked muted
        ch = x["channel"]
        if x["playing_notes"] or any(r["channel"] == ch for r in d["parts"]):
            continue
        c, ns = chans[ch], every[ch]
        keys = [n[2] for n in ns]
        i = ins.get(c.get("insert")) if c.get("insert") is not None else None
        preset = " / ".join(strs(f.plugin_state(ch))[:2]) if c.get("plugin") == "FLEX" else None
        d["parts"].append({"channel": ch, "role": projmusic.classify(c, ns), "name": c.get("name"), "plugin": c.get("plugin"), "sample": None, "preset": preset or None,
                           "insert": c.get("insert"), "insert_name": (i or {}).get("name"), "chain": [s_["plugin"] for s_ in (i or {}).get("slots", [])],
                           "range": [projmusic.note_name(min(keys)), projmusic.note_name(max(keys))], "polyphony": round(projmusic.polyphony(ns), 2),
                           "median_len_beats": None, "notes": 0, "muted_notes": len(ns), "clips": 0, "group": c.get("group"), "muted": True})
    if d["muted_clips"]:
        print("   muted clips", d["muted_clips"], "muted parts", [(x["name"], x["muted_notes"], x["playing_notes"]) for x in d["muted_parts"]][:6], "bounces", bounce[:4])
    ak = AUDIO_KEYS.get(slug(p.stem)[:60]) or next((v for k, v in AUDIO_KEYS.items() if slug(p.stem).startswith(k[:40])), None)
    if ak:
        d["audio_key"] = ak
    if pr and f.main_pitch():
        d["master_pitch_cents"] = f.main_pitch()
    return d


def main():
    for p in sorted(SRC.glob("*.flp")):
        d = data(p)
        (OUT / (slug(p.stem) + ".json")).write_text(json.dumps(d, indent=1, default=str) + "\n", encoding="utf-8")
        print(slug(p.stem), len(d["parts"]), len(d["drums"]), len(d["automation"]))


if __name__ == "__main__":
    main()
