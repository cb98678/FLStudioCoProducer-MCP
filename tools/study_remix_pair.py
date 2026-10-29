"""Study a remix against its original (skill remix-craft, references/study-protocol.md): line map, tempo and key change, 8-bar energy.

    python tools/study_remix_pair.py --original sandbox\\songs\\SONG --remix sandbox\\songs\\SONG_REMIXER [--out sandbox\\remix_study\\SONG\\REMIXER.md]
    python tools/study_remix_pair.py --original-audio FILE --remix-audio FILE --name SONG --remixer NAME   # analyses both first

Each folder is a build_song_analysis folder (song_analysis.json, vocal_words.json, song.wav). With audio files instead, it runs
build_song_analysis on each (stems, grid, words: a few minutes per song on the GPU). The page leaves the anchor, the harmony, the form in
functions and the move that makes the remix work for the reading by ear.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "src"))

from coproducer import dsp, remixstudy  # noqa: E402


def analyse(audio: str, name: str, title: str) -> Path:
    """Run build_song_analysis on one file and return its folder."""
    from coproducer.servers.common import make_session
    s = make_session(HOME, "study_remix_pair", "fl-bridge", "A2")
    r = s.registry.call("build_song_analysis", input_path=audio, name=name, title=title)
    if not r.ok:
        sys.exit("analysis of %s failed: %s" % (audio, r.error))
    return Path(r.value["files"]["analysis"]).parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--original", default="")
    ap.add_argument("--remix", default="")
    ap.add_argument("--original-audio", default="")
    ap.add_argument("--remix-audio", default="")
    ap.add_argument("--name", default="song")
    ap.add_argument("--remixer", default="remix")
    ap.add_argument("--title", default="")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    a.name, a.remixer = (re.sub(r"[^a-z0-9_]+", "_", x.lower()).strip("_") or "x" for x in (a.name, a.remixer))   # analysis folder names
    orig_dir = Path(a.original) if a.original else analyse(a.original_audio, a.name, a.title)
    remix_dir = Path(a.remix) if a.remix else analyse(a.remix_audio, "%s_%s" % (a.name, a.remixer), a.title)
    orig, remix = remixstudy.load(orig_dir), remixstudy.load(remix_dir)
    mapping = remixstudy.map_lines(orig, remix)
    mix = remix_dir / "song.wav"
    x, rate = dsp.load_audio(str(mix if mix.is_file() else remix["song"]))
    blks = remixstudy.with_vocals(remixstudy.blocks(x, rate, remix["bars"], remix["bpm"]), mapping["timeline"])
    text = remixstudy.report(orig, remix, mapping, blks, "%s: %s" % (a.title or orig["title"], a.remixer))
    out = Path(a.out) if a.out else HOME / "sandbox" / "remix_study" / a.name / ("%s.md" % a.remixer)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    (out.with_suffix(".json")).write_text(json.dumps({"mapping": mapping, "blocks": blks, "tempo": remixstudy.tempo_change(orig["bpm"], remix["bpm"])},
                                                     indent=1), encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
