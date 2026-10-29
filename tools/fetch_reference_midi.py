"""Download reference MIDI files of a song (found in the research step on MIDI World and similar sites) into the song's folder, keeping only
real MIDI files. Ask the person before downloading (source and size); they approved MIDI World links on 2026-10-25.

    python tools/fetch_reference_midi.py sandbox\\songs\\NAME URL [URL ...]

Each file lands in sandbox\\songs\\NAME\\reference_midi\\ under its server-given name (or the URL's last part). build_song_plan then tests every
file against the record (midiref.fit) and uses the best accepted one; refused files stay listed in the plan with the reason.
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from pathlib import Path

MAX_BYTES = 2_000_000  # a song MIDI is tens of kilobytes; anything far bigger is not one


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("song_folder")
    ap.add_argument("urls", nargs="+")
    a = ap.parse_args()
    folder = Path(a.song_folder)
    if "sandbox" not in [p.lower() for p in folder.resolve().parts]:
        print("refusing: the song folder must be under a folder named sandbox")
        return 1
    out = folder / "reference_midi"
    out.mkdir(parents=True, exist_ok=True)
    bad = 0
    for url in a.urls:
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (coproducer research step)"}), timeout=60)
            data = r.read(MAX_BYTES + 1)
        except Exception as e:  # noqa: BLE001 - every failure is reported and the next URL tried
            print("%s failed: %s" % (url, e))
            bad += 1
            continue
        name = re.findall(r'filename="?([^";]+)', r.headers.get("Content-Disposition") or "")
        name = re.sub(r"[^A-Za-z0-9_.-]+", "_", (name[0] if name else url.rstrip("/").rsplit("/", 1)[-1]) or "reference")
        if not name.lower().endswith((".mid", ".midi")):
            name += ".mid"
        if data[:4] != b"MThd" or len(data) > MAX_BYTES:
            print("%s is not a MIDI file (%d bytes, starts %r); not kept" % (url, len(data), data[:16]))
            bad += 1
            continue
        (out / name).write_bytes(data)
        print("%s -> %s (%d bytes)" % (url, out / name, len(data)))
    return 1 if bad == len(a.urls) else 0


if __name__ == "__main__":
    sys.exit(main())
