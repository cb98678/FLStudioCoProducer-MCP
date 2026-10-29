"""Solo renders of the demo songs' parts, for the sound study. Run on the host from C:\\coproducer:

    .venv\\Scripts\\python.exe tools\\demo_study\\solo.py build     # sandbox\\demo_study\\solo\\*.flp from the render copies
    .venv\\Scripts\\python.exe tools\\demo_study\\solo.py measure   # describe every sandbox\\demo_study\\solo_wav\\*.wav

build: for every part in sandbox\\demo_study\\solo_plan.json (tools/demo_study/solo_plan.py), a copy of the song's render copy (sandbox\\demo_study\\render, the not-owned plugins
already emptied) with only that part's channels on (plus its Layer, controllers and automation clips, partmix.keep_on), the master's
effects off, and the playlist cut to the part's window and moved to the start (flpfile.window_playlist), so the render is 8 to 16 bars.
measure: soundbrief.describe and soundbrief.starting_point for every solo render, into sandbox\\demo_study\\solo_measure.json.
Nothing here opens FL; the originals are never read except as the render copies already are.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from coproducer import flpfile, partmix, soundbrief  # noqa: E402

STUDY = ROOT / "sandbox" / "demo_study"
PLAN = json.loads((ROOT / "sandbox" / "demo_study" / "solo_plan.json").read_text(encoding="utf-8"))
SERUM_ROLE = {"bass": "bass", "lead": "lead", "arp": "pluck", "chords": "chords", "pad": "pad", "kick": "kick"}


def safe(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", s or "").strip("_")[:28]


def unmute(g: flpfile.Flp, chans: set) -> int:
    """Clear the muted flag on every playlist clip whose pattern holds notes of these channels. Returns how many clips it unmuted."""
    pats = {pid for pid, notes in g.pattern_notes().items() if any(n[1] in chans for n in notes)}
    n = 0

    def fix(it: bytes) -> bytes:
        nonlocal n
        ref = int.from_bytes(it[6:8], "little")
        if ref > flpfile.PATTERN_BASE and ref - flpfile.PATTERN_BASE in pats and g.item_muted(it):
            b = bytearray(it)
            flags = int.from_bytes(b[flpfile.ITEM_FLAGS_AT:flpfile.ITEM_FLAGS_AT + 2], "little") & ~flpfile.ITEM_MUTED
            b[flpfile.ITEM_FLAGS_AT:flpfile.ITEM_FLAGS_AT + 2] = flags.to_bytes(2, "little")
            n += 1
            return bytes(b)
        return it
    g.map_playlist(fix)
    return n


def redo() -> int:
    """After build: copy the solo projects whose render is missing or was made for another window into solo_redo, and drop their stale rows
    from solo_measure.json (and rows of parts no longer planned), so a render of solo_redo and a measure pass bring the study up to date."""
    import shutil
    index = json.loads((STUDY / "solo_index.json").read_text(encoding="utf-8"))
    dst = STUDY / "solo_measure.json"
    done = json.loads(dst.read_text(encoding="utf-8")) if dst.is_file() else {}
    stale = [k for k, v in index.items() if k not in done or done[k].get("window") != v["window"]]
    keep = {k: v for k, v in done.items() if k in index and k not in stale}
    again = [k for k, v in keep.items() if not v.get("silent") and not (v.get("describe") or {}).get("notes")]   # describe found no notes: read it again
    keep = {k: v for k, v in keep.items() if k not in again}
    out = STUDY / (sys.argv[2] if len(sys.argv) > 2 else "solo_redo")
    out.mkdir(parents=True, exist_ok=True)
    for k in stale:
        shutil.copyfile(STUDY / "solo" / (k + ".flp"), out / (k + ".flp"))
    dst.write_text(json.dumps(keep, indent=1, default=str), encoding="utf-8")
    print("redo", len(stale), "measure again", len(again), "kept", len(keep), "dropped", len(done) - len(keep) - len(again))
    for k in stale:
        print(" ", k)
    return 0


def build() -> int:
    out = STUDY / "solo"
    out.mkdir(parents=True, exist_ok=True)
    index = {}
    for song, sp in PLAN.items():
        src = STUDY / "render" / (song + ".flp")
        if not src.is_file():
            print("NO RENDER COPY", song)
            continue
        base = flpfile.Flp.load(src)
        bar = base.ppq * 4
        for n, part in enumerate(sp["parts"]):
            g = flpfile.Flp(base.head, [[e, v] for e, v in base.events], base.tail)
            w = part["window"]
            a = (w["start_bar"] - 1) * bar
            cut = g.window_playlist(a, a + w["bars"] * bar)
            if part.get("unmute"):   # the part's MIDI is muted in the song (bounced to audio): unmute its own clips to hear the patch
                cut["unmuted"] = unmute(g, set(part["channels"]))
            keep = partmix.keep_on(g, part["channels"])
            for ch in g.channel_ids():
                g.set_enabled(ch, ch in keep)
            for slot in range(10):
                g.set_slot_enabled(0, slot, False)
            name = "%s__%02d_%s_%s" % (song[:40], n, part["role"], safe(part["name"]))
            (out / (name + ".flp")).write_bytes(g.to_bytes())
            index[name] = {"song": song, **part, "playlist": cut}
            print(name, cut)
    (STUDY / "solo_index.json").write_text(json.dumps(index, indent=1), encoding="utf-8")
    return 0


def measure() -> int:
    index = json.loads((STUDY / "solo_index.json").read_text(encoding="utf-8"))
    done = {}
    dst = STUDY / "solo_measure.json"
    if dst.is_file():
        done = json.loads(dst.read_text(encoding="utf-8"))
    for name, part in index.items():
        wav = STUDY / "solo_wav" / (name + ".wav")
        if not wav.is_file() or name in done:
            continue
        try:
            x, rate = soundbrief.load_slice(str(wav))
            d = soundbrief.describe(x, rate)
            peak = float(abs(x).max())
            if peak < 1e-3:   # -60 dBFS: nothing played (a muted clip, a part that needs another part, a plugin that rendered nothing)
                done[name] = {"song": part["song"], "role": part["role"], "name": part["name"], "window": part["window"], "silent": True, "unmuted": bool(part.get("unmute")),
                              "peak_db": round(20 * __import__("math").log10(max(peak, 1e-9)), 1)}
                print("SILENT", name)
                dst.write_text(json.dumps(done, indent=1, default=str), encoding="utf-8")
                continue
            row = {"song": part["song"], "role": part["role"], "name": part["name"], "names": part.get("names"), "plugins": part["plugins"],
                   "window": part["window"], "unmuted": bool(part.get("unmute")), "for_option": part.get("for_option"), "peak_db": round(20 * __import__("math").log10(max(peak, 1e-9)), 1), "describe": d}
            if d.get("notes") and part["role"] != "kick":
                try:
                    row["serum_start"] = soundbrief.starting_point(d, SERUM_ROLE.get(part["role"], ""), part["name"] or "")
                except Exception as e:  # noqa: BLE001
                    row["serum_start_error"] = str(e)
            done[name] = row
            print(name, (d.get("words") or d.get("reason")))
        except Exception as e:  # noqa: BLE001
            done[name] = {"song": part["song"], "role": part["role"], "name": part["name"], "error": str(e)}
            print("FAIL", name, e)
        sys.stdout.flush()
        dst.write_text(json.dumps(done, indent=1, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit({"build": build, "redo": redo}.get((sys.argv[1:] or ["measure"])[0], measure)())
