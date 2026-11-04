"""Small FL projects that hold audio files on a song's grid, so a Newtime or Newtone session, the chunks of a vocal or a set of stems can be
opened later and adjusted by hand (the person, 2026-11-03: save every Newtime and Newtone session and every element worked on, in the song's
folder, even if it is a bunch of .flp files).

A bench project (any project with an audio clip on playlist row 1, the one the Newtime and Newtone runs open from) is copied with its other
channels removed, its tempo set to the vocal's, and one sampler channel per file, each placed at its start on the song's clock. The files are
referenced, not copied: the .zpw (Newtime) and .zpa (Newtone) analysis files sit beside their wavs and FL reads them when the editor opens.
"""
from __future__ import annotations

import json
from pathlib import Path

import soundfile as sf

from . import flpfile


def _seconds_to_ticks(s: float, bpm: float, ppq: int) -> int:
    return int(round(s * bpm / 60.0 * ppq))


def _prune(f: "flpfile.Flp", base: int) -> int:
    """Leave only the bench's audio channel (the other channels, their notes and the playlist go); returns the audio channel's new id."""
    f.clear_playlist()
    gone = {c for c in f.channel_ids() if c != base}
    f.strip_notes(gone)
    for c in sorted(gone):
        f.remove_channel(c)
    return f.renumber_channels()[base]


def _channel_for(f: "flpfile.Flp", base: int, index: int, clip: dict) -> int:
    ch = base if index == 0 else f.channel_ids()[-1] + 1
    if index:
        f.clone_channel(base, ch, clip.get("name") or Path(clip["file"]).stem)
    f.set_sample(ch, str(Path(clip["file"]).resolve()), clip.get("name") or Path(clip["file"]).stem)
    if f.stretch_settings(ch)["time"]:
        f.set_stretch(ch, 0.0)           # the files already run at the song's tempo
    return ch


def write_project(bench: str, out_path: str, bpm: float, clips: list[dict]) -> dict:
    """Write out_path: the bench at bpm with one clip per entry of clips {file, name, start_s (0), row (0), length_s (the whole file)}.
    The first clip takes the bench's own audio channel, so Newtime and Newtone open from row 1 as they do on the bench."""
    f = flpfile.Flp.load(bench)
    seen = f.audio_clips(True)
    if not seen or not clips:
        raise ValueError("the bench needs an audio clip to copy and there must be a clip to place")
    template = f.audio_item(seen[0]["channel"])
    base = _prune(f, seen[0]["channel"])
    f.set_tempo(bpm)
    try:
        f.set_song_mode(True)
    except flpfile.FlpError:
        pass
    placed = []
    for i, c in enumerate(clips):
        ch = _channel_for(f, base, i, c)
        dur = float(c.get("length_s") or sf.info(c["file"]).duration)
        start = float(c.get("start_s", 0.0))
        skip = max(0.0, -start)                    # a chunk that begins before the song's clock: its first seconds are left out of the clip
        pos, n = _seconds_to_ticks(max(0.0, start), bpm, f.ppq), _seconds_to_ticks(dur - skip, bpm, f.ppq)
        f.add_audio_clips(ch, int(c.get("row", 0)), [(pos, n, skip * 1000.0, dur * 1000.0)], template)
        placed.append({"channel": ch, "name": c.get("name"), "file": Path(c["file"]).name, "start_s": start, "length_s": round(dur, 3)})
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    f.save(out_path)
    return {"path": str(out_path), "bpm": bpm, "clips": placed}


def chunk_clips(man: dict, c: dict) -> list[dict]:
    """The clips of one chunk's Newtime project, row by row: 1 the file Newtime last opened (its .zpw holds the markers; open Newtime from
    this clip), 2 the chunk as cut, 3 the fitted copy that went into the song. A chunk Newtime skipped has only the last two rows' files."""
    p = Path(c["file"])
    ins = sorted(p.parent.glob(p.stem + "_q*_newtime_in.wav"))
    fitted = p.with_name(p.stem + "_q" + p.suffix)
    rows = ([(ins[-1], "%s Newtime in (markers)" % p.stem)] if ins else []) + [(p, "%s as cut" % p.stem)] + ([(fitted, "%s fitted" % p.stem)] if fitted.is_file() else [])
    return [{"file": str(f), "name": n, "row": i, "start_s": 0.0, "length_s": None} for i, (f, n) in enumerate(rows) if Path(f).is_file()]


def newtone_clips(src: str, tuned: str) -> list[dict]:
    """The Newtone project: row 1 the file Newtone opened (its .zpa holds the tuning; open Newtone from this clip), row 2 the tuned result."""
    rows = [(src, "%s Newtone in (tuning)" % Path(src).stem), (tuned, "%s tuned" % Path(tuned).stem)]
    return [{"file": f, "name": n, "row": i} for i, (f, n) in enumerate(rows) if Path(f).is_file()]


def chunk_projects(man_path: str, bench: str, out_dir: str) -> list[dict]:
    """One Newtime project per chunk of a manifest into out_dir, named STEM_NN_newtime.flp; returns what was written."""
    man = json.loads(Path(man_path).read_text(encoding="utf-8"))
    out = []
    for c in man["chunks"]:
        name = Path(c["file"]).stem + "_newtime.flp"
        out.append(write_project(bench, str(Path(out_dir) / name), float(man["bpm"]), chunk_clips(man, c)))
    return out


def set_projects(man_path: str, bench: str, out_dir: str, beds: list[str], fitted: str = "", tuned: str = "") -> list[dict]:
    """The stage projects of a vocal, each on the song's clock at the vocal's tempo: every chunk as cut (and with the fitted copies), the joined
    fitted voice, the tuned voice, with the beds (instrumental stems) under them on the rows below."""
    man = json.loads(Path(man_path).read_text(encoding="utf-8"))
    bpm, d = float(man["bpm"]), Path(out_dir)
    under = [{"file": b, "name": Path(b).stem, "row": 20 + i} for i, b in enumerate(beds) if Path(b).is_file()]

    def tiles(suffix: str, row: int) -> list[dict]:
        out = []
        for c in man["chunks"]:
            p = Path(c["file"])
            f = p.with_name(p.stem + suffix + p.suffix) if suffix else p
            if f.is_file():
                out.append({"file": str(f), "name": f.stem, "row": row, "start_s": c["grid_s"], "length_s": c["end_s"] - c["grid_s"]})
        return out

    jobs = {"01_vocal_chunks_cut.flp": tiles("", 0), "02_vocal_chunks_fitted.flp": tiles("_q", 0)}
    if fitted:
        jobs["03_vocal_fitted_joined.flp"] = [{"file": fitted, "name": Path(fitted).stem, "row": 0}]
    if tuned:
        jobs["04_vocal_tuned.flp"] = [{"file": tuned, "name": Path(tuned).stem, "row": 0}]
    return [write_project(bench, str(d / n), bpm, c + under) for n, c in jobs.items() if c]


def newtone_project(bench: str, out_dir: str, src: str, tuned: str) -> dict:
    """The Newtone session's project, SRC_STEM_newtone.flp, at the bench's tempo (the vocal's own)."""
    bpm = flpfile.Flp.load(bench).tempo()
    return write_project(bench, str(Path(out_dir) / (Path(tuned).stem + "_newtone.flp")), bpm, newtone_clips(src, tuned))


def write_readme(out_dir: str) -> str:
    """projects/README.txt: every project under out_dir (read back from the files), what it holds, and how to open the editors from it."""
    lines = ["FL projects saved by the vocal pipeline. Files are referenced, not copied: keep the wavs and their .zpw / .zpa analysis files where they are.", "",
             "newtime/  one per chunk. Row 1 is the file Newtime last opened: clip menu > Time-warp sample shows the markers as left (checked: they come back); press F2 and set the sample tempo to the bpm listed below first (Newtime shows its own guess), adjust, Ctrl+S saves a wav.",
             "          Rows 2 and 3 are the chunk as cut and the fitted copy that went into the song.",
             "newtone/  the Newtone session. Row 1 is the file Newtone opened (its tuning in the .zpa), row 2 the tuned result.",
             "stages/   the whole vocal on the song's clock at each stage, with the instrumental under it.", ""]
    for f in sorted(Path(out_dir).glob("*/*.flp")):
        fl = flpfile.Flp.load(str(f))
        names = [fl.channel_info(c)["name"] for c in fl.channel_ids()]
        lines.append("%s/%s  %g bpm  %s" % (f.parent.name, f.name, fl.tempo(), "; ".join(names)))
    p = Path(out_dir) / "README.txt"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(p)
