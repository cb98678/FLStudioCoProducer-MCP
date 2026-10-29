from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from coproducer.result import Result, fail, ok

STOP = frozenset("a an and are as at be but by for from i in is it me my of on or so the to we you your".split())


def find_song_clues(input_path: str, words_file: str = "") -> Result:
    """The facts a web search needs to name a song: the file name, the title, artist and album tags (ffprobe, when installed), and the run of
    two to six words its transcript repeats most (a chorus line is the usual title), with search queries built from them. The research step
    (skill remix-from-stems) then looks up the song's form and favourite parts and saves them with write_song_notes. Errors: E_NOT_FOUND.
    """
    p = Path(input_path)
    if not p.is_file():
        return fail("E_NOT_FOUND", "no file at %s" % p.name)
    tags = {}
    if shutil.which("ffprobe"):
        done = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(p)], capture_output=True, text=True, check=False)
        raw = json.loads(done.stdout or "{}").get("format", {}).get("tags", {}) if done.returncode == 0 else {}
        tags = {k.lower(): v for k, v in raw.items() if k.lower() in ("title", "artist", "album", "date", "album_artist")}
    name = re.sub(r"[_\-.]+", " ", p.stem).strip()
    line = _repeated_line(words_file) if words_file and Path(words_file).is_file() else ""
    queries = [q for q in (" ".join(filter(None, (tags.get("title"), tags.get("artist")))), name if not tags.get("title") else "",
                           ('"%s" song' % line) if line else "") if q]
    return ok({"file_name": name, "tags": tags, "repeated_line": line, "queries": queries})


def _repeated_line(words_file: str) -> str:
    """The run of two to six words, starting and ending on a content word, that the transcript repeats most (count times length), at least 3 times."""
    ws = [re.sub(r"[^a-z']", "", str(w["word"]).lower()) for w in json.loads(Path(words_file).read_text(encoding="utf-8"))["words"]]
    ws = [w for w in ws if w]
    counts: dict = {}
    for n in range(2, 7):
        for i in range(len(ws) - n + 1):
            run = ws[i : i + n]
            if run[0] not in STOP and run[-1] not in STOP:
                counts[" ".join(run)] = counts.get(" ".join(run), 0) + 1
    good = [(c * len(k.split()), k) for k, c in counts.items() if c >= 3]
    return max(good)[1] if good else ""
