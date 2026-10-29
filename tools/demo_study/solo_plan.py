"""Pick the parts of each demo song worth rendering solo (the synth and sampler parts and the main kick), group layers that play the same
notes into one stack, and choose a window for each: the section where the stack plays most, up to 16 bars and 40 s. A part whose MIDI is all
muted (bounced to audio) is kept and marked unmute, and every instrument in the option bank gets a solo of its own.
Writes sandbox/demo_study/solo_plan.json. python tools/demo_study/solo_plan.py [--flp-dir sandbox/demo_study/flp]"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
from coproducer import anatomy, flpfile, projmusic  # noqa: E402
import gen_demo_options as G  # noqa: E402

ARGS = dict(zip(sys.argv[1::2], sys.argv[2::2]))
SRC = Path(ARGS.get("--flp-dir", ROOT / "sandbox" / "demo_study" / "flp"))
PLAN = ROOT / "sandbox" / "demo_study" / "solo_plan.json"
ROLES = ("bass", "lead", "arp", "chords", "pad")
MAX_PER_SONG = 8


def slug(stem):
    return re.sub(r"[^A-Za-z0-9]+", "_", stem.encode("ascii", "ignore").decode()).strip("_")[:60]


def plan_song(p):
    f = flpfile.Flp.load(p)
    rep = anatomy.read(f)
    m = projmusic.read(f, rep)
    notes = projmusic.song_notes(f)
    for c in rep["channels"]:
        if c.get("type") == "layer" and notes.get(c["id"]):
            for kid in c.get("children") or []:
                notes[kid] = sorted(notes.get(kid, []) + [(n[0], kid, n[2], n[3], n[4]) for n in notes[c["id"]]])
    secs = m["sections"]
    bpm = f.tempo()
    bar_s = 240.0 / bpm
    max_bars = max(4, min(16, int(40.0 / bar_s)))
    chans = {c["id"]: c for c in rep["channels"]}
    stacks = defaultdict(list)
    info = {}
    for pp in m["parts"]:
        ch = pp["channel"]
        ns = notes.get(ch) or []
        if pp["role"] not in ROLES or len(ns) < 8 or not (pp["plugin"] or pp["sample"]):
            continue
        if projmusic.drum_voice(pp["name"] or "") or projmusic.drum_voice(pp["sample"] or "") or pp["plugin"] in ("Fruity DrumSynth Live", "Fruity Slicer", "Slicex", "FPC"):
            continue  # a drum the classifier took for a tonal part: the kick row covers drum design
        sig = tuple(sorted({(round(n[0], 2), n[2]) for n in ns}))[:400]
        stacks[sig].append(ch)
        info[ch] = pp
    kicks = [pp for pp in m["parts"] if pp["role"] == "drums" and (projmusic.drum_voice(pp["name"] or "") == "kick") and len(notes.get(pp["channel"]) or []) >= 8]
    rows = []
    for sig, chs in stacks.items():
        lead = max(chs, key=lambda c: len(notes[c]))
        rows.append({"channels": sorted(chs), "role": info[lead]["role"], "name": info[lead]["name"], "plugins": sorted({info[c]["plugin"] or "sampler" for c in chs}),
                     "notes": len(notes[lead])})
    rows.sort(key=lambda r: -r["notes"])
    rows = rows[:MAX_PER_SONG]
    if kicks:
        k = max(kicks, key=lambda pp: len(notes[pp["channel"]]))
        rows.append({"channels": [k["channel"]], "role": "kick", "name": k["name"], "plugins": [k["plugin"] or "sampler"], "notes": len(notes[k["channel"]])})
    for r in rows:
        ns = [n for c in r["channels"] for n in notes.get(c, [])]
        best = None
        for start in range(1, m["bars"] + 1, 4):          # the densest stretch of max_bars on a 4-bar grid
            a, b = (start - 1) * 4, (start - 1 + max_bars) * 4
            cnt = sum(1 for n in ns if a <= n[0] < b)
            if cnt and (best is None or cnt > best[0]):
                best = (cnt, start)
        if best is None:
            r["window"] = None
            continue
        sec = next((s for s in secs if s["start_bar"] <= best[1] < s["start_bar"] + s["bars"]), {})
        r["window"] = {"start_bar": best[1], "bars": max_bars, "section": sec.get("name") or sec.get("kind") or "", "notes": best[0]}
        r["names"] = [chans[c].get("name") for c in r["channels"]]
    return {"bpm": bpm, "ppq": f.ppq, "parts": [r for r in rows if r.get("window")]}


SOURCES = json.loads((ROOT / "src" / "coproducer" / "data" / "options" / "sources.json").read_text(encoding="utf-8"))["songs"]


def sound_parts(p, plan):
    """A solo for every sound option of this song that the plan does not cover yet, so each instrument in the bank gets measured."""
    f = flpfile.Flp.load(p)
    playing, every = projmusic.song_notes(f), projmusic.song_notes(f, muted=True)
    names = {f.channel_info(c)["name"]: c for c in f.channel_ids()}
    have = {c for r in plan["parts"] for c in r["channels"]}
    max_bars = max(4, min(16, int(40.0 / (240.0 / f.tempo()))))
    bars = int(max((n[0] for ns in every.values() for n in ns), default=0) // 4) + 1
    out = []
    for sid_, song, chan_names, role, *_rest in G.SOUNDS:
        if not G.same_song(SOURCES[song]["data"], slug(p.stem)):
            continue
        chs = sorted(names[n] for n in chan_names if n in names)
        if not chs or set(chs) & have:
            continue
        unmute = not any(playing.get(c) for c in chs)
        ns = [n for c in chs for n in (every if unmute else playing).get(c, [])]
        best = None
        for start in range(1, bars + 1, 4):
            a, b = (start - 1) * 4, (start - 1 + max_bars) * 4
            cnt = sum(1 for n in ns if a <= n[0] < b)
            if cnt and (best is None or cnt > best[0]):
                best = (cnt, start)
        if not best:
            continue
        info = [f.channel_info(c) for c in chs]
        out.append({"channels": chs, "role": {"stab": "chords", "sub": "bass"}.get(role, role), "name": info[0]["name"], "plugins": [], "notes": len(ns),
                    "window": {"start_bar": best[1], "bars": max_bars, "section": "", "notes": best[0]}, "names": [i["name"] for i in info],
                    "for_option": sid_, **({"unmute": True} if unmute else {})})
        have |= set(chs)
    return out


def muted_parts(p, plan):
    """Parts whose MIDI is all muted in the playlist (a producer bounced them to audio): stacks of channels playing the same muted notes,
    windowed on those notes and marked unmute, so the solo copy unmutes their own clips and the patch can be heard."""
    f = flpfile.Flp.load(p)
    rep = anatomy.read(f)
    playing, every = projmusic.song_notes(f), projmusic.song_notes(f, muted=True)
    have = {c for r in plan["parts"] for c in r["channels"]}
    chans = {c["id"]: c for c in rep["channels"]}
    stacks = defaultdict(list)
    for ch, ns in every.items():
        c = chans.get(ch) or {}
        if ch in have or playing.get(ch) or len(ns) < 8 or not (c.get("plugin") or c.get("sample")) or c.get("type") in ("automation", "layer"):
            continue
        if projmusic.drum_voice(c.get("name") or "") or projmusic.drum_voice(c.get("sample") or ""):
            continue
        stacks[tuple(sorted({(round(n[0], 2), n[2]) for n in ns}))[:400]].append(ch)
    max_bars = max(4, min(16, int(40.0 / (240.0 / f.tempo()))))
    bars = int(max((n[0] for ns in every.values() for n in ns), default=0) // 4) + 1
    out = []
    for chs in stacks.values():
        lead = max(chs, key=lambda c: len(every[c]))
        ns = [n for c in chs for n in every[c]]
        best = max(((sum(1 for n in ns if (st - 1) * 4 <= n[0] < (st - 1 + max_bars) * 4), -st) for st in range(1, bars + 1, 4)), default=(0, -1))
        best = (best[0], -best[1])                                    # the earliest of equally dense stretches
        role = projmusic.classify(chans[lead], every[lead])
        if best[0] and role in ROLES:
            out.append({"channels": sorted(chs), "role": role, "name": chans[lead].get("name"),
                        "plugins": sorted({chans[c].get("plugin") or "sampler" for c in chs}), "notes": len(every[lead]), "unmute": True,
                        "window": {"start_bar": best[1], "bars": max_bars, "section": "", "notes": best[0]}, "names": [chans[c].get("name") for c in sorted(chs)]})
    return sorted(out, key=lambda r: -r["notes"])[:MAX_PER_SONG]


def main():
    out = {}
    for p in sorted(SRC.glob("*.flp")):
        plan = out[slug(p.stem)] = plan_song(p)
        plan["parts"] += muted_parts(p, plan)
        plan["parts"] += sound_parts(p, plan)
        print(slug(p.stem), len(plan["parts"]), [(r["role"], r["name"], len(r["channels"])) for r in plan["parts"]])
    PLAN.write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
