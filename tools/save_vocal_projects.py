"""Save the vocal's work as FL projects in the song's folder, so every element can be opened and adjusted by hand later.

    python tools/save_vocal_projects.py --manifest sandbox/songs/NAME/warped/chunks/chunks.json --bench sandbox/songs/NAME/gui/bench_117.flp
        [--out sandbox/songs/NAME/projects] [--bed other_117.wav ...] [--fitted vocal_fitted.wav] [--tuned vocal_tuned.wav] [--newtone-in vocal_fitted.wav]

Writes OUT/newtime/STEM_NN_newtime.flp (one per chunk: the file Newtime last opened on row 1, the chunk as cut, the fitted copy),
OUT/stages/ (the chunks tiled on the song's clock as cut and fitted, the joined fitted voice, the tuned voice, with the beds under them),
OUT/newtone/ (the Newtone session) and OUT/README.txt. vocal_gui_run.py does the Newtime and Newtone ones by itself after each run; this
backfills a song worked on before and builds the stage projects. Everything must sit under a folder named sandbox. Skill vocal-chunking.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from coproducer import sessionflp  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--bench", required=True)
    ap.add_argument("--out", default="")
    ap.add_argument("--bed", action="append", default=[])
    ap.add_argument("--fitted", default="")
    ap.add_argument("--tuned", default="")
    ap.add_argument("--newtone-in", default="")
    a = ap.parse_args()
    out = Path(a.out) if a.out else Path(a.bench).resolve().parents[1] / "projects"
    if any("sandbox" not in Path(p).resolve().parts for p in (a.manifest, a.bench, str(out))):
        print("everything must sit under a folder named sandbox", file=sys.stderr)
        return 2
    written = sessionflp.chunk_projects(a.manifest, a.bench, str(out / "newtime"))
    written += sessionflp.set_projects(a.manifest, a.bench, str(out / "stages"), a.bed, a.fitted, a.tuned)
    if a.tuned and a.newtone_in:
        written.append(sessionflp.newtone_project(a.bench, str(out / "newtone"), a.newtone_in, a.tuned))
    print("wrote %d projects under %s" % (len(written), out))
    print("readme:", sessionflp.write_readme(str(out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
