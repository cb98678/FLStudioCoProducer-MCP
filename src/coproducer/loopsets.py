"""A song's loops, kit and patterns as files, and the search for matching loops on this computer (skill loops-and-kits; the signal work is in
loopkit). extract() reads a build_song_analysis folder and writes under one output folder: drums/, bass/, music/ and full/ loops (every
repetition aligned and averaged), kit/ one-shots, midi/ patterns and bass lines, vocal/ a hook cut, patterns.json and README.md. find()
ranks loop files against one section's patterns and kick files against the kit's kick. Neither writes anywhere but the output folder.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import soundfile as sf

from . import loopkit

STEMS = ("drums", "bass", "other", "instrumental", "vocals")
LOOP_DIRS = (("drums", "drums"), ("bass", "bass"), ("other", "music"), ("instrumental", "full"))
MARGIN_S = 0.03          # a one-shot ends this long before the next hit's grid time (hats are often pushed early)
PACK_LOOPS = ("Loops", "Legacy/Loops")
PACK_KICKS = ("Drums/Kicks", "Legacy/Drums/Dance", "Legacy/Drums/FPC/Kick Drums")
AUDIO_EXT = (".wav", ".flac", ".ogg", ".aif", ".aiff")


class LoopError(ValueError):
    pass


def parse_sections(text) -> list[tuple[str, int, int]]:
    """"name:a-b,name:a-b" (bars 1-based, inclusive) or [[name, a, b], ...]."""
    if isinstance(text, (list, tuple)):
        return [(str(n), int(a), int(b)) for n, a, b in text]
    out = []
    for part in str(text).split(","):
        try:
            name, rng = part.split(":")
            a, b = (int(v) for v in rng.split("-"))
        except ValueError as e:
            raise LoopError("sections are name:first-last, comma separated (%r)" % part) from e
        if not 1 <= a <= b:
            raise LoopError("section %s: bars count from 1 and the last is not before the first" % name)
        out.append((name.strip(), a, b))
    if not out:
        raise LoopError("no sections")
    return out


def stem_path(folder: Path, given: str) -> Path | None:
    """The stem file: the path the analysis recorded, or the same path under this analysis folder (a copy moved elsewhere)."""
    p = Path(given)
    if p.is_file():
        return p
    parts = Path(given.replace("\\", "/")).parts
    for i in range(len(parts)):
        q = folder.joinpath(*parts[i:])
        if q.is_file():
            return q
    return None


def _write(path: Path, x: np.ndarray, rate: int, peak_db: float = -1.0) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    pk = float(np.max(np.abs(x))) or 1.0
    sf.write(str(path), (x / pk * 10 ** (peak_db / 20)).astype(np.float32), rate, subtype="PCM_24")
    return str(path)


def gap_s(steps: list[int], others: list[int], step_s: float) -> float:
    """Time from a voice's hit to the next hit of any of the others (around the bar): how long its one-shot may ring alone."""
    best = 16
    for s in steps:
        for o in others:
            d = (o - s) % 16
            if d:
                best = min(best, d)
    return best * step_s


def extract(song_dir: str | Path, sections, out_dir: str | Path, name: str = "", loop_bars=(1, 2, 4), kit_from: str = "", hook: str = "") -> dict:
    """Write the loops, kit and patterns of the given sections and return the report (also written as patterns.json and README.md)."""
    folder = Path(song_dir)
    info = json.loads((folder / "song_analysis.json").read_text(encoding="utf-8"))
    name = name or info.get("name") or folder.name
    out = Path(out_dir)
    grid = info["grid"]
    bpm = float(grid["bpm"])
    paths = {k: stem_path(folder, v) for k, v in (info.get("stems") or {}).items() if k in STEMS}
    paths = {k: p for k, p in paths.items() if p}
    if "drums" not in paths:
        raise LoopError("the analysis has no drum stem on this computer")
    audio = {k: sf.read(str(p), dtype="float64", always_2d=True) for k, p in paths.items()}
    level = {k: float(np.sqrt(np.mean(v[0] ** 2))) or 1e-9 for k, v in audio.items()}
    rate = int(audio["drums"][1])
    dur = len(audio["drums"][0]) / rate
    edges = loopkit.regular_edges(grid["bars"], bpm, dur) if grid.get("steady") else loopkit.bar_edges(grid["bars"], bpm, dur)
    drums_m = audio["drums"][0].mean(axis=1)
    envs = loopkit.band_envelopes(drums_m, rate)
    secs = parse_sections(sections)
    if any(b > len(edges) - 1 for _n, _a, b in secs):
        raise LoopError("a section runs past the song's last bar (%d)" % (len(edges) - 1))
    tag = ("%g" % round(bpm, 2)).replace(".", "p")
    rep: dict = {"name": name, "bpm": bpm, "bar_s": round(240.0 / bpm, 4), "first_bar_s": round(float(edges[0]), 3), "stems": sorted(paths),
                 "sections": {}, "kit": {}, "files": []}
    for sec, b0, b1 in secs:
        rep["sections"][sec] = _section(audio, level, rate, edges, envs, sec, b0, b1, [int(n) for n in loop_bars], out, name, tag, bpm, rep["files"])
    kit_sec = kit_from or max(secs, key=lambda s: s[2] - s[1])[0]
    if kit_sec not in rep["sections"]:
        raise LoopError("kit_from names no section: %s" % kit_sec)
    for k, (shot, si) in _kit(audio["drums"][0], drums_m, rate, edges, envs, rep["sections"][kit_sec], bpm).items():
        f = out / "kit" / ("%s_%s.wav" % (name, k))
        rep["files"].append(_write(f, loopkit.fade_tail(shot, rate), rate))
        rep["kit"][k] = {**si, **loopkit.shot_features(shot, rate), "file": f.name, "from": kit_sec}
    if hook and "vocals" in audio:
        h0, h1 = (int(v) for v in str(hook).split("-"))
        v, vr = audio["vocals"]
        seg = v[int(edges[h0 - 1] * vr):int(edges[min(h1, len(edges) - 1)] * vr)]
        f = out / "vocal" / ("%s_hook_bars%d-%d_%sbpm.wav" % (name, h0, h1, tag))
        rep["files"].append(_write(f, loopkit.loop_ends(seg, int(vr), 8.0), int(vr)))
        rep["hook"] = {"bars": [h0, h1], "file": f.name}
    out.mkdir(parents=True, exist_ok=True)
    (out / "patterns.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
    (out / "README.md").write_text(readme(rep), encoding="utf-8")
    return rep


def _section(audio, level, rate, edges, envs, sec, b0, b1, lens, out, name, tag, bpm, files) -> dict:
    bars = list(range(b0 - 1, b1))
    same = loopkit.matching_bars(envs, rate, edges, bars)
    if len(same) < max(2, len(bars) // 2):   # a section that changes bar to bar (a break): read and average all of it
        same = bars
    dp = loopkit.drum_patterns(envs, rate, edges, same)
    row: dict = {"bars": [b0, b1], "used_bars": [b + 1 for b in same], "drums": dp["patterns"], "profiles": dp["profiles"], "loops": {}}
    best_bass = 99.0
    for n in lens:
        starts = [b for b in bars[::n] if b + n - 1 <= bars[-1] and b in same]   # in phase with the section start (the chord loop's bar 1)
        for stem, sub in LOOP_DIRS:
            if not starts or stem not in audio or (stem != "drums" and n == 1):
                continue
            try:
                loop, li = loopkit.average_loop(audio[stem][0], rate, edges, starts, n)
            except ValueError:
                continue
            key = "%s_%d" % (sub, n)
            if float(np.sqrt(np.mean(loop ** 2))) < level[stem] * 10 ** (-24 / 20):   # the stem is out here (the bass in a break)
                row["loops"][key] = {"silent": True}
                continue
            if li["n"] > 1 and li["residual_db"] > -3.0:   # what plays here does not repeat (bleed, or a part that changes every bar)
                row["loops"][key] = {**li, "skipped": "does not repeat"}
                continue
            f = out / sub / ("%s_%s_%dbar_%sbpm.wav" % (name, sec, n, tag))
            files.append(_write(f, loopkit.loop_ends(loop, rate), rate))
            row["loops"][key] = {**li, "file": f.name}
            if stem == "bass" and (li["n"] > 1 or "bass_notes" not in row) and li["residual_db"] < best_bass:
                row["bass_notes"], row["bass_bars"], best_bass = loopkit.bass_notes(loop, rate, bpm), n, li["residual_db"]   # the length that repeats best
    midi = out / "midi"
    midi.mkdir(parents=True, exist_ok=True)
    if row.get("bass_notes"):
        notes = [(nt["step"] / 4.0, nt["steps"] / 4.0 * 0.95, nt["midi"], 100) for nt in row["bass_notes"]]
        files.append(str(loopkit.write_midi(midi / ("%s_%s_bass.mid" % (name, sec)), {"bass": notes}, bpm)))
    voices = {k: dp["patterns"][k] for k in ("kick", "snare", "hat")}
    files.append(str(loopkit.write_midi(midi / ("%s_%s_drums.mid" % (name, sec)), {"drums " + sec: loopkit.pattern_notes(voices, 4)}, bpm)))
    return row


def _kit(x, drums_m, rate, edges, envs, row, bpm) -> dict:
    """{voice: (one-shot, info)} from a section's matching bars: the kick where no clap lands on it, the snare or clap (the kick taken out
    when it always lands on one), the hat off the kick."""
    bars = [b - 1 for b in row["used_bars"]]
    pats = row["drums"]
    hits = {k: [i for i, c in enumerate(p) if c == "X"] for k, p in pats.items()}
    loud = {k: [i for i, c in enumerate(p) if c in "Xx"] for k, p in pats.items()}
    step_s = 240.0 / bpm / 16
    fast = loopkit._env(drums_m, rate, 1.0)   # the full-band attack: where a kick or clap really starts (its low band rises 20 ms later)
    shots: dict = {}
    clear = [s for s in hits["kick"] if pats["snare"][s] != "X"]       # no clap or snare on it (its own click may show as x there)
    kick_steps = [s for s in clear if s % 4 == 0] or clear or hits["kick"]   # on the beat first: the off-beat hits of a dembow are often a perc
    if kick_steps:
        clean = max(0.06, gap_s(kick_steps, loud["snare"] + loud["hat"], step_s) - MARGIN_S)        # alone until the next other hit
        ln = min(0.6, max(clean, gap_s(kick_steps, loud["kick"], step_s) - MARGIN_S))           # its tail, low-passed past `clean`
        kick, ki = loopkit.average_hits(x, rate, loopkit.hit_times(fast, rate, edges, bars, kick_steps), ln)
        shots["kick"] = (loopkit.lowpass_tail(kick, rate, clean), {**ki, "steps": kick_steps, "length_s": round(ln, 3), "clean_s": round(clean, 3)})
    snare_steps = [s for s in hits["snare"] if s not in hits["kick"]] or hits["snare"]   # off the kick when it plays there (a dembow perc)
    if snare_steps:
        others = [o for o in loud["kick"] + loud["hat"] if o not in snare_steps]
        ln = min(0.6, max(0.08, gap_s(snare_steps, others, step_s) - MARGIN_S))
        on_kick = all(s in loud["kick"] for s in snare_steps) and "kick" in shots
        sn, si = loopkit.average_hits(x, rate, loopkit.hit_times(fast if on_kick else envs["snare"], rate, edges, bars, snare_steps), ln)
        if on_kick:   # cut where the kick starts, so the kick inside lines up with the kick one-shot, and take it out
            sn, si["kick_subtracted"] = loopkit.subtract(sn, shots["kick"][0], rate)
        mm = sn.mean(axis=1)
        body = float(np.sqrt(np.mean(loopkit._band(mm, rate, 150, 300) ** 2))) or 1e-9
        crack = float(np.sqrt(np.mean(loopkit._band(mm, rate, 1000, 4000) ** 2))) or 1e-9
        ratio = 20 * math.log10(body / crack)
        shots["snare" if ratio > -6 else "clap"] = (sn, {**si, "steps": snare_steps, "length_s": round(ln, 3), "body_vs_crack_db": round(ratio, 1)})
    hat_steps = [s for s in hits["hat"] if s not in hits["kick"]] or hits["hat"]
    if hat_steps:
        ln = min(0.6, max(0.06, gap_s(hat_steps, loud["kick"] + loud["snare"], step_s) - MARGIN_S))
        ht, hi = loopkit.average_hits(x, rate, loopkit.hit_times(envs["hat"], rate, edges, bars, hat_steps), ln)
        shots["ohat" if loopkit.shot_features(ht, rate)["decay_ms"] > 90 else "hat"] = (ht, {**hi, "steps": hat_steps, "length_s": round(ln, 3)})
    return shots


def note_name(m: int) -> str:
    return "%s%d" % (("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")[m % 12], m // 12 - 1)


def readme(rep: dict) -> str:
    L = ["# Loops and kit: %s" % rep["name"], "",
         "Cut from the song's separated stems at %g bpm (one bar is %.3f s; bar 1 starts at %.3f s). Every loop is the median of all the"
         " repetitions of that pattern in the section, aligned on their onsets, so what does not repeat (the vocal's bleed, fills) is left"
         " out: the residual is how loud the left-out part was against the loop (lower: more bleed removed). Drum patterns read three bands:"
         " kick below 110 Hz, snare or clap 1.2 to 4 kHz, hats above 7 kHz (X accent, x normal, o soft). Kit voices are named by measurement:"
         " check them by ear." % (rep["bpm"], rep["bar_s"], rep["first_bar_s"]), "",
         "In FL Studio: drag a loop onto the playlist (or a Sampler channel), then in its channel settings set Time stretching TIME to Project"
         " tempo (right-click the knob) with mode e3 Generic, or load it in Slicex to play its slices from the piano roll; drag a kit file onto"
         " the channel rack for a Sampler channel and program the pattern below in the step sequencer, or drag the MIDI file from midi/ into"
         " the piano roll of the channel.", ""]
    for sec, row in rep["sections"].items():
        L += ["## %s (bars %d to %d, %d matching bars used)" % (sec, row["bars"][0], row["bars"][1], len(row["used_bars"])), "",
              "| Band | Pattern |", "| --- | --- |"]
        L += ["| %s | `%s` |" % (k, v) for k, v in row["drums"].items()]
        kx = {i for i, c in enumerate(row["drums"]["kick"]) if c == "X"}
        for k in ("snare", "hat"):
            hx = {i for i, c in enumerate(row["drums"][k]) if c == "X"}
            if hx and hx <= kx:
                L.append("| | the %s band only hits with the kick here: probably the kick's own click, not a %s |" % (k, k))
        if row.get("bass_notes"):
            L += ["", "Bass notes (%d-bar loop: 16th step from the loop start + length in 16ths, note in scientific names where MIDI 60 is"
                  " C4; FL's piano roll calls that key C5): %s" % (row.get("bass_bars", 2),
                                                                     ", ".join("%d+%d %s" % (n["step"], n["steps"], note_name(n["midi"])) for n in row["bass_notes"]))]
        L += ["", "| Loop | Repeats averaged | Residual | File |", "| --- | --- | --- | --- |"]
        for k, li in row["loops"].items():
            how = "silent here" if li.get("silent") else li.get("skipped") or ("single cut, not averaged" if li.get("n") == 1 else "%.1f dB" % li["residual_db"])
            L.append("| %s | %s | %s | %s |" % (k, li.get("n", "-"), how, li.get("file", "-")))
        L.append("")
    if rep["kit"]:
        L += ["## Kit (from %s)" % next(iter(rep["kit"].values()))["from"], "", "| Voice | Hits averaged | Steps | Length | Pitch | Decay | File |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
        for k, v in rep["kit"].items():
            L.append("| %s | %d | %s | %d ms | %s | %s ms | %s |" % (k, v["n"], " ".join(str(s + 1) for s in v["steps"]), int(1000 * v["length_s"]),
                                                               ("%.0f Hz" % v["pitch_hz"]) if v.get("pitch_hz") else "-", v["decay_ms"], v["file"]))
        L.append("")
    if rep.get("hook"):
        L += ["Vocal hook: bars %d to %d, %s (cut, not averaged)." % (rep["hook"]["bars"][0], rep["hook"]["bars"][1], rep["hook"]["file"]), ""]
    return "\n".join(L)


# ---- finding loops and kicks

def fl_packs(fl_exe: str | None = None) -> Path | None:
    """FL Studio's factory Packs folder (next to the FL executable: Data\\Patches\\Packs), or None."""
    if not fl_exe:
        from .cli import detect
        found = detect.newest_fl_exe()
        fl_exe = str(found) if found else None
    p = Path(fl_exe).parent / "Data" / "Patches" / "Packs" if fl_exe else None
    return p if p and p.is_dir() else None


def audio_files(folders: list) -> list[Path]:
    out = []
    for f in folders:
        f = Path(f)
        if f.is_dir():
            out += sorted(p for p in f.rglob("*") if p.suffix.lower() in AUDIO_EXT)
    return out


def _ogg_in_wav(path: Path) -> bytes | None:
    """The Ogg stream inside a WAV whose format tag is one of the Ogg Vorbis modes (0x674F to 0x6771: how FL Studio ships its factory
    loops, slice markers and all), or None."""
    raw = Path(path).read_bytes()
    if raw[:4] != b"RIFF" or raw[8:12] != b"WAVE":
        return None
    i, tag, data = 12, None, None
    while i + 8 <= len(raw):
        cid, size = raw[i:i + 4], int.from_bytes(raw[i + 4:i + 8], "little")
        if cid == b"fmt ":
            tag = int.from_bytes(raw[i + 8:i + 10], "little")
        elif cid == b"data":
            data = raw[i + 8:i + 8 + size]
        i += 8 + size + (size & 1)
    if tag is None or not 0x674F <= tag <= 0x6771 or not data:
        return None
    k = data.find(b"OggS")
    return data[k:] if k >= 0 else None


def _read(path: Path, seconds: float) -> tuple[np.ndarray, int]:
    """The first seconds of an audio file. FL's factory loops are Ogg Vorbis inside a WAV wrapper (format tag 0x674F), which libsndfile
    and ffmpeg refuse as WAV: the Ogg stream inside is read instead."""
    try:
        info = sf.info(str(path))
        x, rate = sf.read(str(path), frames=int(seconds * info.samplerate), dtype="float64", always_2d=True)
        return x, int(rate)
    except RuntimeError as err:
        import io
        ogg = _ogg_in_wav(path)
        if ogg is None:
            raise
        try:
            with sf.SoundFile(io.BytesIO(ogg)) as f:
                x = f.read(frames=int(seconds * f.samplerate), dtype="float64", always_2d=True)
                return x, int(f.samplerate)
        except RuntimeError as e2:
            raise RuntimeError("cannot read the Ogg stream in %s: %s" % (path.name, e2)) from err


def find(patterns: dict, section: str, folders: list, kick: str | Path | None = None, kick_folders: list | None = None, top: int = 10) -> dict:
    """{"target", "loops": [{file, score, bpm, bars, patterns}] best first, "kicks": [{file, distance, ...}] nearest first, "unreadable"}
    for one section of an extract() report."""
    if section not in patterns.get("sections", {}):
        raise LoopError("no section %r in the patterns (%s)" % (section, ", ".join(patterns.get("sections", {}))))
    target = patterns["sections"][section]
    loops, bad = [], []
    for p in audio_files(folders):
        try:
            x, rate = _read(p, 30.0)
            d = loopkit.describe_loop(x, rate)
        except (RuntimeError, ValueError):
            bad.append(str(p))
            continue
        loops.append({"file": str(p), "score": loopkit.similarity(target, d), "bpm": d["bpm"], "bars": d["bars"], "patterns": d["patterns"]})
    loops.sort(key=lambda r: -r["score"])
    kicks, want = [], None
    if kick:
        kx, kr = _read(Path(kick), 1.0)
        want = loopkit.shot_features(kx, kr)
        for p in audio_files(kick_folders or []):
            try:
                x, rate = _read(p, 1.5)
            except RuntimeError:
                bad.append(str(p))
                continue
            f = loopkit.shot_features(x, rate)
            kicks.append({"file": str(p), "distance": loopkit.kick_distance(want, f), **f})
        kicks.sort(key=lambda r: r["distance"])
    return {"section": section, "target": target["drums"], "loops": loops[:top], "searched": len(loops), "kick_target": want, "kicks": kicks[:top],
            "unreadable": bad}


def found_markdown(res: dict, name: str, folders: list) -> str:
    t = res["target"]
    L = ["# Loops like %s, section %s" % (name, res["section"]), "",
         "Searched (read only): %s, %d loops. Target: kick `%s`, snare or clap `%s`, hats `%s`. Score 1.0 is the same step profile in all"
         " three bands; tempo is not compared (FL stretches a loop to the project tempo)." % (", ".join(str(f) for f in folders) or "nothing",
                                                                                            res["searched"], t["kick"], t["snare"], t["hat"]), "",
         "| Score | File | Tempo | Bars | Kick | Snare or clap | Hats |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for r in res["loops"]:
        L.append("| %.3f | %s | %g | %g | `%s` | `%s` | `%s` |" % (r["score"], Path(r["file"]).name, r["bpm"], r["bars"], r["patterns"]["kick"],
                                                             r["patterns"]["snare"], r["patterns"]["hat"]))
    if res.get("kick_target"):
        k = res["kick_target"]
        L += ["", "## Kicks nearest the song's kick (pitch %s Hz, decay %s ms, click %s Hz)" % (k.get("pitch_hz"), k.get("decay_ms"), k.get("centroid_hz")), "",
              "| Distance | File | Pitch | Decay | Click |", "| --- | --- | --- | --- | --- |"]
        for r in res["kicks"]:
            L.append("| %.2f | %s | %s Hz | %s ms | %s Hz |" % (r["distance"], Path(r["file"]).name, r.get("pitch_hz"), r.get("decay_ms"), r.get("centroid_hz")))
    return "\n".join(L) + "\n"
