"""A reference MIDI file of the song (MIDI World and sites like it publish fan transcriptions with piano, bass, guitars and drums), checked
against the record before anything is taken from it, and turned into clean harmony for the remix's synths.

Rule from the person (2026-10-25): use such files as the baseline for the instrumentation so the synths keep the song's cadence and its
actual chords; not every file is right, so each is tested first; and where chords are dense or several guitars pile up, bring them down to
roots and simple triads so nothing sounds muddy.

What is taken, and why not more: fan transcriptions follow the record's harmony but rarely its exact form (the first file tried had the
first verse on piano alone, no solo section, and a different number of choruses), so notes are not copied bar for bar. Taken are (1) the
chord quality heard over each bass root (major, minor, or a bare fifth when the file is ambiguous or crowded) and (2) the rhythm guitar's
most common one-bar strum, so the remix's chords sit on the record's own bar-aligned roots with the song's cadence.

The test: the file's key against the record's (pitch-class profile), and its bass roots against the record's bass roots at the best bar
offset and transposition. A file is accepted when the roots agree on at least MIN_ROOT_MATCH of the compared bars.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

MIN_ROOT_MATCH = 0.6
MIN_PAIRS = 16
NAMES = "C C# D D# E F F# G G# A A# B".split()
BASS_PROGRAMS, HARMONY_PROGRAMS = range(32, 40), set(range(0, 8)) | set(range(16, 32)) | set(range(40, 56)) | set(range(88, 96))


def read(path: str) -> dict:
    """{"tpb", "beats_per_bar", "tempo_bpm" (the first tempo), "tracks": [{"name", "program", "channel", "role", "notes": [(beat, end_beat,
    pitch, velocity)]}]} with role drums (channel 10), bass, harmony or other."""
    import io
    import re

    import mido

    raw = Path(path).read_bytes()
    # a key signature with a mode byte other than 0 (major) or 1 (minor) stops mido (the MIDI World "Girls" file has 255): read it as major
    raw = re.sub(rb"\xff\x59\x02(.)[\x02-\xff]", lambda mt: b"\xff\x59\x02" + mt.group(1) + b"\x00", raw, flags=re.S)
    m = mido.MidiFile(file=io.BytesIO(raw))
    tpb, bpb, tempo = m.ticks_per_beat, 4, None
    tracks = []
    for t in m.tracks:
        name, prog, chans, on, notes, tick = "", None, set(), {}, [], 0
        for msg in t:
            tick += msg.time
            if msg.type == "track_name":
                name = msg.name.strip()
            elif msg.type == "program_change" and prog is None:
                prog = msg.program
            elif msg.type == "time_signature" and tick == 0:
                bpb = msg.numerator * 4 // msg.denominator
            elif msg.type == "set_tempo" and tempo is None:
                tempo = mido.tempo2bpm(msg.tempo)
            elif msg.type == "note_on" and msg.velocity > 0:
                on[(msg.channel, msg.note)] = (tick, msg.velocity)
                chans.add(msg.channel)
            elif msg.type in ("note_off", "note_on") and (msg.channel, msg.note) in on:
                t0, v = on.pop((msg.channel, msg.note))
                notes.append((t0 / tpb, tick / tpb, msg.note, v))
        if notes:
            tracks.append({"name": name, "program": prog or 0, "channel": min(chans), "notes": sorted(notes)})
    for tr in tracks:
        tr["role"] = role(tr)
    return {"tpb": tpb, "beats_per_bar": bpb, "tempo_bpm": round(tempo or 120.0, 2), "tracks": tracks}


def role(tr: dict) -> str:
    name = tr["name"].lower()
    pitches = [n[2] for n in tr["notes"]]
    if tr["channel"] == 9 or "drum" in name or "perc" in name:
        return "drums"
    if "bass" in name or tr["program"] in BASS_PROGRAMS or (pitches and np.median(pitches) < 45):
        return "bass"
    if tr["program"] in HARMONY_PROGRAMS or any(w in name for w in ("piano", "guitar", "organ", "keys", "string", "pad")):
        return "harmony"
    return "other"


def bar_roots(notes: list[tuple], beats_per_bar: int, n_bars: int) -> list:
    """The pitch class sounding longest in each bar (None under a fifth of a bar of notes)."""
    out = []
    for b in range(n_bars):
        lo, hi = b * beats_per_bar, (b + 1) * beats_per_bar
        w = np.zeros(12)
        for t0, t1, p, _v in notes:
            ov = min(t1, hi) - max(t0, lo)
            if ov > 0:
                w[p % 12] += ov
        if w.sum() <= 0.2 * beats_per_bar:
            out.append(None)
            continue
        top = int(np.argmax(w))
        if w[(top - 7) % 12] >= 0.75 * w[top]:  # root and fifth about even (a bass voice singing F and C): the root is the lower of the pair
            top = (top - 7) % 12
        out.append(top)
    return out


def _notes(midi: dict, roles: tuple) -> list[tuple]:
    return [n for t in midi["tracks"] if t["role"] in roles for n in t["notes"]]


def bar_beats(midi: dict, source_bpm: float) -> float:
    """The file's beats per bar of the record: a file notated at double the record's tempo (MIDI World's "Girls": 292.8 against 139.4 bpm)
    spends twice the beats on a bar, one at half the tempo half as many."""
    r = midi["tempo_bpm"] / source_bpm if source_bpm else 1.0
    bpb = midi["beats_per_bar"]
    return bpb * 2 if 1.8 <= r <= 2.2 else bpb / 2 if 0.45 <= r <= 0.55 else bpb


def low_voices(midi: dict) -> list[tuple]:
    """The notes that carry the roots: the bass track, else low harmony, else the low notes of any pitched track (a sung bass voice)."""
    return (_notes(midi, ("bass",)) or [n for n in _notes(midi, ("harmony",)) if n[2] < 55]
            or [n for n in _notes(midi, ("other",)) if n[2] < 60])


def profile(midi: dict) -> np.ndarray:
    w = np.zeros(12)
    for t0, t1, p, _v in _notes(midi, ("bass", "harmony", "other")):
        w[p % 12] += t1 - t0
    return w / (w.sum() or 1.0)


def fit(midi: dict, audio_roots: dict, key_pc: int, source_bpm: float) -> dict:
    """How well the file matches the record: the best (bar offset, transposition) of its bass roots against the record's ({source bar:
    pitch class}), the share of compared bars that agree there, and whether that and the key agree well enough to use it. A reason is
    given when it is refused."""
    bpb = bar_beats(midi, source_bpm)
    bass = low_voices(midi)
    if not bass:
        return {"accepted": False, "why": "no bass line or low voice to compare"}
    n_bars = int(max(n[1] for n in bass) // bpb) + 1
    mr = bar_roots(bass, bpb, n_bars)
    lo, hi = min(audio_roots), max(audio_roots)
    best = (0.0, 0, 0, 0)
    for tr in range(12):
        for k in range(-(hi - lo) - 8, n_bars + 8):
            pairs = [(mr[b + k], r) for b, r in audio_roots.items() if r is not None and 0 <= b + k < n_bars and mr[b + k] is not None]
            if len(pairs) >= MIN_PAIRS:
                sc = sum(1 for x, y in pairs if (x + tr) % 12 == y) / len(pairs)
                if (round(sc, 3), len(pairs), -min(tr, 12 - tr)) > (round(best[0], 3), best[3], -min(best[2], 12 - best[2])):  # then the most bars compared
                    best = (sc, k, tr, len(pairs))
    score, k, tr, n = best
    prof = np.roll(profile(midi), tr)
    in_key = float(sum(prof[(key_pc + s) % 12] for s in (0, 2, 4, 5, 7, 9, 11)))
    ok = score >= MIN_ROOT_MATCH and in_key >= 0.8
    why = "" if ok else ("bass roots agree on only %.0f%% of %d bars" % (score * 100, n) if score < MIN_ROOT_MATCH else
                         "only %.0f%% of its notes are in the record's key" % (in_key * 100))
    return {"accepted": ok, "why": why, "root_match": round(score, 3), "bars_compared": n, "offset_bars": k, "transpose": tr,
            "in_key_share": round(in_key, 3), "tempo_bpm": midi["tempo_bpm"], "tempo_ratio": round(source_bpm / midi["tempo_bpm"], 3), "bar_beats": bpb}


ACCOMP_TOP = 64  # harmony notes from E4 up are mostly the tune (a piano part often plays the vocal melody): chords are read below it


def chord_qualities(midi: dict, transpose: int = 0, third_share: float = 0.05, bar_beats: float | None = None) -> dict:
    """{root pitch class: "maj" | "min" | "5"} from the accompaniment heard over each bass root (harmony notes below ACCOMP_TOP, transposed
    to the record's key): major or minor when that third clearly outweighs the other, a bare fifth when the file is unclear or crowded."""
    bpb = bar_beats or midi["beats_per_bar"]
    bass = low_voices(midi)
    harm = [n for n in _notes(midi, ("harmony",)) if n[2] < ACCOMP_TOP] or [n for n in _notes(midi, ("other",)) if n[2] < ACCOMP_TOP]
    if not bass or not harm:
        return {}
    n_bars = int(max(n[1] for n in bass + harm) // bpb) + 1
    roots = bar_roots(bass, bpb, n_bars)
    acc: dict = {}
    for b, r in enumerate(roots):
        if r is None:
            continue
        w = acc.setdefault((r + transpose) % 12, np.zeros(12))
        for t0, t1, p, _v in harm:
            ov = min(t1, (b + 1) * bpb) - max(t0, b * bpb)
            if ov > 0:
                w[(p + transpose) % 12] += ov
    out = {}
    for r, w in acc.items():
        w = w / (w.sum() or 1.0)
        mi, ma = w[(r + 3) % 12], w[(r + 4) % 12]
        if ma < third_share and mi < third_share:
            continue  # no third heard at all: leave the quality to the key (a riff of roots and fifths says nothing about it)
        out[r] = "maj" if ma >= third_share and ma > 1.5 * mi else "min" if mi >= third_share and mi > 1.5 * ma else "5"
    return out


def strum(midi: dict, steps: int = 16, bar_beats: float | None = None) -> str:
    """The rhythm guitar's (the harmony track with the most onsets in bars where the drums play) most common one-bar pattern on a 16th
    grid, as a pattern string: X on beats it accents, x elsewhere, . for rests. Falls back to quarter notes."""
    bpb = bar_beats or midi["beats_per_bar"]
    drums = {int(n[0] // bpb) for n in _notes(midi, ("drums",))}
    best, best_n = None, 0
    pitched = [t for t in midi["tracks"] if t["role"] == "harmony"] or [t for t in midi["tracks"] if t["role"] == "other"]  # a riff when no chords
    for t in pitched:
        n = sum(1 for x in t["notes"] if int(x[0] // bpb) in drums)
        if n > best_n:
            best, best_n = t, n
    if best is None:
        return "x...x...x...x..."
    bars: dict = {}
    for t0, _t1, _p, v in best["notes"]:
        b = int(t0 // bpb)
        if b in drums:
            s = int(round((t0 - b * bpb) / bpb * steps)) % steps
            bars.setdefault(b, {})
            bars[b][s] = max(bars[b].get(s, 0), v)
    pats: dict = {}
    for row in bars.values():
        loud = max(row.values())
        key = "".join(("X" if row[s] >= 0.9 * loud else "x") if s in row else "." for s in range(steps))
        pats[key] = pats.get(key, 0) + 1
    return max(pats, key=lambda p: (pats[p], -p.count("x") - p.count("X"))) if pats else "x...x...x...x..."


def voicing(root_pc: int, quality: str, low: int = 57, high: int = 69) -> list[int]:
    """At most three notes inside low..high (A3 to A4 by default): a close triad, or root and fifth for a bare fifth. Clear, never muddy."""
    steps = {"maj": (0, 4, 7), "min": (0, 3, 7), "5": (0, 7)}[quality]
    out = []
    for s in steps:
        p = low + (root_pc + s - low) % 12
        out.append(p if p <= high else p - 12)
    return sorted(set(out))
