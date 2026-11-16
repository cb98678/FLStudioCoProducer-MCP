"""Support parts written the way a session keyboardist and arranger would (skill session-arranger, 2026-11-06).

The person (2026-11-06), after hearing her voice and guitar transcribed note for note: "you try to use math to replicate notes you
heard in the music exactly and it sounds terrible". The song is read for four things only: the key, the chord of each bar, where the
singer sings and rests (on the 16th grid), and how busy each phrase is (syllables per beat). Nothing heard is copied. The parts:

* keys and pad, the harmonic anchor: sustained chords under a busy vocal, a soft broken-chord figure tucked in the background under a
  spacious one, voiced under her range, at most four notes at once (three under a busy vocal), led to the nearest inversion;
* bass, the rhythm-section anchor: one groove cell per section, locked to the 16th grid, roots with fifths and octaves, an approach
  note into the next chord only at phrase ends and section changes;
* the answer line, call and response: a few notes only in the gaps where she rests (an 8th after she stops, an 8th before she comes
  back), never in every gap, above her range.

Syncopation comes only from the named cells in CELLS. Velocities follow beat strength (VEL), never flat and never 127. check() measures
every rule on the notes written, so a part that breaks one is found before anyone hears it. Notes are (start_beat, dur_beats, key,
velocity) on the song's grid, beat 0 at its first downbeat.
"""
from __future__ import annotations

import hashlib

import numpy as np

from . import vocalchops, vocalchunk

NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
FLATS = {"Db": 1, "Eb": 3, "Gb": 6, "Ab": 8, "Bb": 10}
MAJOR, MINOR = (0, 2, 4, 5, 7, 9, 11), (0, 2, 3, 5, 7, 8, 10)
BUSY, SPACIOUS = 1.5, 0.75          # syllables per beat over a two-bar phrase: over BUSY the keys hold, under SPACIOUS they move gently
# velocity by 16th position in the bar: beat 1, beat 3, beats 2 and 4, the other 8ths, the remaining 16ths
VEL = {0: 104, 8: 96, 4: 88, 12: 88, 2: 76, 6: 76, 10: 76, 14: 76}
VEL_16TH = 64
# groove cells: (16th step, length in 16ths, degree) with degree 1 the root, 5 the fifth, 8 the octave. Each is a deliberate figure,
# the same every bar of a section; nothing off the beat comes from anywhere else.
CELLS = {
    "whole": ((0, 16, 1),),
    "halves": ((0, 8, 1), (8, 8, 1)),
    "halves_fifth": ((0, 8, 1), (8, 8, 5)),
    "quarters": ((0, 4, 1), (4, 4, 1), (8, 4, 1), (12, 4, 1)),
    "eighths": tuple((s, 2, 1) for s in range(0, 16, 2)),
    "eighths_octave": tuple((s, 2, 8 if s in (6, 14) else 1) for s in range(0, 16, 2)),
    "push": ((0, 6, 1), (6, 2, 1), (8, 8, 5)),            # the 'and' of 2 pushes into beat 3 (a Charleston figure)
    "anticipate": ((0, 8, 1), (8, 6, 1), (14, 2, 1)),     # the last 8th of the bar anticipates the next chord (pitch set per bar)
}
LIMITS = {"pad": {"poly": 4, "per_bar": 8, "grid": 0.25}, "keys": {"poly": 2, "per_bar": 8, "grid": 0.5},
          "bass": {"poly": 1, "per_bar": 8, "grid": 0.25}, "answer": {"poly": 1, "per_bar": 4, "grid": 0.5},
          "guide": {"poly": 1, "per_bar": 4, "grid": 0.5}}


def parse_chord(name: str | None) -> tuple[int, str] | None:
    """('F#m') -> (6, 'min'); 'D' -> (2, 'maj'); '5' suffix -> 'pow'; None for no chord."""
    if not name:
        return None
    n = name.strip()
    root = n[:2] if n[:2] in FLATS or (len(n) > 1 and n[1] == "#") else n[:1]
    pc = FLATS[root] if root in FLATS else NAMES.index(root)
    rest = n[len(root):].split("/")[0]
    q = "min" if rest.startswith("m") and not rest.startswith("maj") else "dim" if rest.startswith("dim") else "pow" if rest == "5" else "maj"
    return pc, q


def chord_pcs(pc: int, q: str, third: bool = True) -> list[int]:
    """Pitch classes of a triad; without its third (a sus2 shape, root, 2nd, 5th) when the reading of the third is unsure."""
    if not third or q == "pow":
        return [pc, (pc + 2) % 12, (pc + 7) % 12] if third is False else [pc, (pc + 7) % 12]
    return [pc, (pc + (3 if q in ("min", "dim") else 4)) % 12, (pc + (6 if q == "dim" else 7)) % 12]


def velocity(beat: float, scale: float = 1.0, seed: str = "") -> int:
    """Beat-strength velocity (VEL) scaled for the part, with a small fixed variation from the note's place (never random run to run)."""
    step = int(round((beat % 4) * 4)) % 16
    base = VEL.get(step, VEL_16TH) * scale
    h = int(hashlib.md5(("%s:%.3f" % (seed, beat)).encode()).hexdigest()[:4], 16)
    return int(max(1, min(120, round(base + (h % 7) - 3))))


# ---------------------------------------------------------------- reading the vocal

def vocal_map(x: np.ndarray, rate: int, bpm: float, origin_s: float, beats: int, floor_under_db: float = vocalchunk.FLOOR_UNDER_DB) -> dict:
    """Where she sings, per 16th of the grid (beat 0 at origin_s), and her syllable onsets in beats. A 16th is sung when the 10 ms
    envelope is above the floor (floor_under_db under the loud level, vocalchunk's 30 dB by default; a stem with bleed needs less) for
    at least a third of it."""
    mono = np.asarray(x, float).mean(axis=1) if np.ndim(x) == 2 else np.asarray(x, float)
    env = vocalchunk.envelope(mono, rate)
    floor = vocalchunk.floor_of(env, floor_under_db)
    on = env > floor
    win = vocalchunk.WIN_S
    sung = []
    for i in range(beats * 4):
        a = origin_s + i * 15.0 / bpm
        lo, hi = int(a / win), int((a + 15.0 / bpm) / win)
        seg = on[lo:hi]
        sung.append(bool(len(seg)) and float(np.mean(seg)) >= 0.34)
    runs = vocalchunk.voiced_runs(env, floor, win)
    ons = []
    for t0, t1 in runs:
        if t1 - t0 >= 0.06:
            ons += vocalchops.onsets(mono, rate, max(0.0, t0 - 0.02), t1, 0.09) or [t0]
    beats_on = sorted({round((t - origin_s) * bpm / 60.0, 3) for t in ons if t >= origin_s - 0.05})
    return {"sung": sung, "onsets": beats_on, "floor_db": round(floor, 1)}


def merge_maps(a: dict, b: dict) -> dict:
    """Sung where either map says so (the safe side for the answer line); onsets from the first."""
    return {"sung": [x or y for x, y in zip(a["sung"], b["sung"])], "onsets": a["onsets"], "floor_db": a.get("floor_db")}


def vocal_map_from_notes(notes: list, beats: int) -> dict:
    """The same map from a note list of her voice (start_beat, dur, ...): a reading only, the notes are never played."""
    sung = [False] * (beats * 4)
    for s, d, *_ in notes:
        for i in range(int(s * 4), min(len(sung), int(np.ceil((s + d) * 4)))):
            sung[i] = True
    return {"sung": sung, "onsets": sorted(float(n[0]) for n in notes), "floor_db": None}


def phrase_modes(vmap: dict, bars: int, window: int = 2) -> list[dict]:
    """Per window of bars: syllables per beat, the share of 16ths sung and the keys' mode: 'hold' (busy: long legato chords),
    'move' (spacious: a soft broken-chord figure), 'pulse' (in between: chords re-struck each bar)."""
    out = []
    for b0 in range(0, bars, window):
        b1 = min(bars, b0 + window)
        n = sum(1 for o in vmap["onsets"] if b0 * 4 <= o < b1 * 4)
        rate = n / max(1, (b1 - b0) * 4)
        share = float(np.mean(vmap["sung"][b0 * 16:b1 * 16] or [0]))
        mode = "hold" if rate >= BUSY else "move" if rate <= SPACIOUS or share < 0.3 else "pulse"
        out.append({"bars": [b0, b1], "syllables_per_beat": round(rate, 2), "sung_share": round(share, 2), "mode": mode})
    return out


def gaps(vmap: dict, min_beats: float = 1.0) -> list[tuple[float, float]]:
    """(start, end) beats of every rest in her line at least min_beats long."""
    out, start = [], None
    for i, s in enumerate(vmap["sung"] + [True]):
        if not s and start is None:
            start = i
        elif s and start is not None:
            if (i - start) / 4 >= min_beats:
                out.append((start / 4, i / 4))
            start = None
    return out


def voice_range(notes: list | None, default: tuple[int, int] = (60, 72)) -> tuple[int, int]:
    """Her low and high (10th and 90th percentile of the pitches read), to keep the keys out of her way."""
    if not notes:
        return default
    p = [n[2] for n in notes]
    return int(np.percentile(p, 10)), int(np.percentile(p, 90))


# ---------------------------------------------------------------- writing the parts

def _bar_chords(chords: list[dict], bars: int) -> list[tuple[int, str, bool] | None]:
    """Per bar: (root pc, quality, third sure). A third is unsure when the reading's margin is under 0.1 and the parallel chord is
    among its candidates (A against Am): the keys then leave the third out."""
    out = []
    by_bar = {c["bar"] - 1: c for c in chords}
    last = None
    for b in range(bars):
        c = by_bar.get(b)
        got = parse_chord(c.get("chord")) if c else None
        if got:
            par = NAMES[got[0]] + ("" if got[1] == "min" else "m")
            sure = not (c.get("margin", 1.0) < 0.1 and par in (c.get("cands") or []))
            last = (got[0], got[1], sure)
        out.append(last)
    return out


def _near(pcs: list[int], lo: int, hi: int, prev: list[int] | None) -> list[int]:
    """The chord's tones inside [lo, hi], in the inversion closest to the previous chord (common tones kept, the rest move least)."""
    cands = []
    for base in range(lo, hi - 6):
        if base % 12 not in pcs:
            continue
        v, k = [], base
        for pc in sorted(pcs, key=lambda p: (p - base % 12) % 12):
            while k % 12 != pc:
                k += 1
            v.append(k)
        if v[-1] <= hi:
            cands.append(v)
    if not cands:                     # the range is too narrow for a closed voicing: fold an open one into it
        return sorted(k - 12 if k > hi and k - 12 >= lo - 5 else k for k in (lo + (p - lo) % 12 for p in pcs))
    if not prev:
        return min(cands, key=lambda v: abs(np.mean(v) - (lo + hi) / 2))
    return min(cands, key=lambda v: sum(min(abs(a - b) for b in prev) for a in v))


def keys_parts(chords: list[dict], bars: int, modes: list[dict], voice: tuple[int, int], sections: list[dict] | None = None) -> dict:
    """The pad (held chords) and the keys figure. Under her: the pad's top note stays at least two semitones under her low note.
    hold: one chord per change, held to the next (legato), three notes; pulse: re-struck every bar, four notes; move: the pad thins to
    root and fifth, soft, and the keys play a broken chord in 8ths (root, fifth, third, fifth), quiet, tucked under the pad's top."""
    bc = _bar_chords(chords, bars)
    top = min(voice[0] - 2, 64)
    lo = max(48, top - 14)            # over the bass's octave (C2 to B2): the pad and the bass never share a register
    mode_of = {b: m["mode"] for m in modes for b in range(*m["bars"])}
    pad, keys, prev = [], [], None
    b = 0
    while b < bars:
        if bc[b] is None:
            b += 1
            continue
        mode = mode_of.get(b, "pulse")
        end = b + 1
        if mode == "hold":
            while end < bars and bc[end] == bc[b] and mode_of.get(end) == "hold" and end - b < 4:
                end += 1
        pc, q, sure = bc[b]
        pcs = chord_pcs(pc, q, sure)
        if mode == "move":
            pcs = chord_pcs(pc, q, None)                    # root and fifth only: the figure carries the third
        voiced = _near(pcs, lo, top, prev)
        if mode == "pulse" and len(voiced) == 3 and voiced[0] + 12 <= top:
            voiced = voiced + [voiced[0] + 12]
        prev = voiced
        scale = 0.82 if mode != "move" else 0.62
        for k in voiced:
            pad.append((b * 4.0, (end - b) * 4.0 - 0.05, k, velocity(b * 4.0, scale, "pad%d" % k)))
        if mode == "move":
            tones = _near(chord_pcs(pc, q, sure), lo + 7, top + 3, None)
            figure = [tones[0], tones[-1], tones[1] if len(tones) > 2 else tones[-1], tones[-1]]
            for j in range(8):
                beat = b * 4.0 + j * 0.5
                keys.append((beat, 0.45, figure[j % 4], velocity(beat, 0.68, "keys")))
        b = end
    return {"pad": pad, "keys": keys}


def degree_key(pc: int, q: str, degree: int, lo: int = 36) -> int:
    root = lo + (pc - lo) % 12
    return root + {1: 0, 5: 7, 8: 12}.get(degree, 0) if degree != 5 or q != "dim" else root + 6


def _approach(pc_next: int, key_pcs: tuple[int, ...], lo: int = 36) -> int:
    """A scale step into the next root: the nearest scale tone above or below it that is not the root itself."""
    root = lo + (pc_next - lo) % 12
    cands = [root - d for d in (1, 2)] + [root + d for d in (1, 2)]
    scale = [k for k in cands if k % 12 in key_pcs]
    return min(scale or [root - 1], key=lambda k: (abs(k - root), k > root))


def bass_part(chords: list[dict], bars: int, cell_of_bar, key_pc: int, mode: str = "major", phrase: int = 4, lo: int = 36) -> list[tuple]:
    """One cell per bar (cell_of_bar(bar) -> a CELLS name or None for a rest), roots from the chord table; on the last 8th of a phrase's
    last bar (every `phrase` bars) and of the bar before a section changes cell, the note becomes an approach into the next root."""
    bc = _bar_chords(chords, bars)
    key_pcs = tuple((key_pc + s) % 12 for s in (MAJOR if mode == "major" else MINOR))
    out = []
    for b in range(bars):
        name = cell_of_bar(b)
        if not name or bc[b] is None:
            continue
        pc, q, _ = bc[b]
        nxt = bc[b + 1] if b + 1 < bars else None
        turn = nxt is not None and ((b + 1) % phrase == 0 or cell_of_bar(b + 1) != name)
        for step, length, deg in CELLS[name]:
            beat = b * 4.0 + step / 4.0
            k = degree_key(pc, q, deg, lo)
            if name == "anticipate" and step == 14 and nxt:
                k = degree_key(nxt[0], nxt[1], 1, lo)
            out.append([beat, length / 4.0 * 0.92, k, velocity(beat, 0.95, "bass")])
        if turn and nxt and nxt[0] != pc:
            last = out[-1]
            cut = b * 4.0 + 3.5
            if last[0] < cut - 1e-6:
                last[1] = max(0.25, cut - last[0] - 0.04)
                out.append([cut, 0.46, _approach(nxt[0], key_pcs, lo), velocity(cut, 0.9, "bass")])
            elif abs(last[0] - cut) < 1e-6:
                last[2] = _approach(nxt[0], key_pcs, lo)
    return [tuple(n) for n in out]


SHAPES = ((5, 3, 2, 1), (1, 2, 3, 5), (3, 4, 3, 2), (5, 4, 3), (8, 7, 5), (3, 2, 1))


def answer_part(chords: list[dict], bars: int, vmap: dict, voice: tuple[int, int], key_pc: int, mode: str = "major",
                every: int = 2, min_gap: float = 1.5, max_notes: int = 4, seed: str = "answer") -> tuple[list[tuple], list[dict]]:
    """Call and response: a short figure of scale tones (SHAPES, degrees over the bar's root) in her rests of at least min_gap beats,
    an 8th after she stops and an 8th before she returns, in 8ths, the last note held; at most one figure in `every` rests and never
    two in one bar. Above her high note. Returns the notes and the rests used."""
    bc = _bar_chords(chords, bars)
    scale = [(key_pc + s) % 12 for s in (MAJOR if mode == "major" else MINOR)]
    lo = max(voice[1] + 3, 69)
    notes, used, last_bar, k = [], [], -9, 0
    for g0, g1 in gaps(vmap, min_gap):
        a = np.ceil((g0 + 0.5) * 2) / 2
        z = g1 - 0.5
        bar = int(a // 4)
        if z - a < 1.0 or bar >= bars or bc[min(bar, bars - 1)] is None or bar == last_bar:
            continue
        k += 1
        if k % every:
            continue
        pc = bc[bar][0]
        root = lo + (pc - lo) % 12
        shape = SHAPES[int(hashlib.md5(("%s%d" % (seed, bar)).encode()).hexdigest()[:2], 16) % len(SHAPES)]
        n = min(max_notes, len(shape), int((z - a) / 0.5))
        keyset = sorted(root - 24 + o for o in range(0, 37) if (root - 24 + o) % 12 in scale)
        targets = [root + {1: 0, 2: 2, 3: 4, 4: 5, 5: 7, 7: 11, 8: 12}[d] for d in shape[:n]]
        if max(targets) > lo + 10 and min(targets) - 12 >= voice[1] + 1:
            targets = [x - 12 for x in targets]      # keep the figure near the bottom of the space over her, not shrill
        for j in range(n):
            target = targets[j]
            p = min(keyset, key=lambda x: abs(x - target))
            beat = float(a + j * 0.5)
            dur = 0.45 if j < n - 1 else float(max(0.45, min(1.5, z - beat)))
            notes.append((beat, dur, p, velocity(beat, 0.78, seed)))
        used.append({"from": float(a), "to": float(min(z, a + 0.5 * (n - 1) + 1.5)), "bar": bar + 1, "notes": n})
        last_bar = bar
    return notes, used


def guide_melody(notes: list, key_pc: int, mode: str = "major", window: float = 2.0, min_sung: float = 0.5) -> list[tuple]:
    """Only when the person asks for one: a simplified guide of her line, the main held note of each half bar (the pitch she holds longest
    in it, snapped to the key), started on the 8th grid and held while she sings, repeats joined. Her ornaments, slides and quick
    passing notes are left out: at most two notes a bar. A reading of her line made playable, not a transcription."""
    scale = {(key_pc + st) % 12 for st in (MAJOR if mode == "major" else MINOR)}
    snap = lambda k: k if k % 12 in scale else min((k - 1, k + 1), key=lambda x: (x % 12 not in scale, x))
    out: list[list] = []
    end = max((n[0] + n[1] for n in notes), default=0.0)
    w = 0.0
    while w < end:
        inside = [(max(w, n[0]), min(w + window, n[0] + n[1]), int(n[2])) for n in notes if n[0] < w + window and n[0] + n[1] > w]
        sung = sum(b - a for a, b, _ in inside)
        if inside and sung >= min_sung:
            held: dict[int, float] = {}
            for a, b, k in inside:
                held[k] = held.get(k, 0.0) + b - a
            k = snap(max(held, key=lambda x: (held[x], -x)))
            a = float(np.ceil(min(x[0] for x in inside) * 2 - 1e-6) / 2)
            z = float(np.floor(max(x[1] for x in inside) * 2 + 1e-6) / 2)
            if z - a >= 0.5:
                if out and out[-1][2] == k and a - (out[-1][0] + out[-1][1]) <= 0.25:
                    out[-1][1] = z - out[-1][0]
                else:
                    out.append([a, z - a, k, velocity(a, 0.72, "guide")])
        w += window
    return [(a, d - 0.05, k, v) for a, d, k, v in out]


# ---------------------------------------------------------------- the checks

WRITTEN_ROLES = ("pad", "keys", "bass", "answer", "guide")   # the parts the arranger writes; a pack's own parts keep their accents


def max_poly(notes: list[tuple]) -> int:
    ev = sorted([(s, 1) for s, d, *_ in notes] + [(s + d - 1e-6, -1) for s, d, *_ in notes], key=lambda e: (e[0], e[1]))
    cur = best = 0
    for _, e in ev:
        cur += e
        best = max(best, cur)
    return best


def check(parts: dict, vmap: dict, cells_used: dict | None = None) -> dict:
    """Every rule measured: polyphony, notes per bar, starts on the part's grid, bass starts only where its cells put them, velocity
    following beat strength (downbeats louder than the rest, a spread of at least 5, none at 127), answer notes only where she rests."""
    out, fails = {}, []
    for role, notes in parts.items():
        if not notes:
            continue
        lim = LIMITS.get(role, {"poly": 4, "per_bar": 16, "grid": 0.25})
        poly = max_poly(notes)
        per_bar = max(np.bincount([int(s // 4) for s, *_ in notes]))
        off_grid = sum(1 for s, *_ in notes if abs(s / lim["grid"] - round(s / lim["grid"])) > 1e-6)
        v = np.array([n[3] for n in notes], float)
        down = [n[3] for n in notes if abs(n[0] % 4) < 1e-6]
        rest = [n[3] for n in notes if abs(n[0] % 1) > 1e-6]
        r = {"notes": len(notes), "max_poly": poly, "max_per_bar": int(per_bar), "off_grid": off_grid, "vel_spread": round(float(v.std()), 1),
             "vel_max": int(v.max()), "downbeat_vs_offbeat": round(float(np.mean(down) - np.mean(rest)), 1) if down and rest else None}
        if poly > lim["poly"]:
            fails.append("%s: %d notes at once (limit %d)" % (role, poly, lim["poly"]))
        if per_bar > lim["per_bar"]:
            fails.append("%s: %d notes in one bar (limit %d)" % (role, per_bar, lim["per_bar"]))
        if off_grid:
            fails.append("%s: %d starts off its %s-beat grid" % (role, off_grid, lim["grid"]))
        if v.max() >= 127 or (len(v) > 8 and v.std() < 5 and role != "pad"):
            fails.append("%s: flat or maxed velocities" % role)
        if r["downbeat_vs_offbeat"] is not None and r["downbeat_vs_offbeat"] <= 0 and role in WRITTEN_ROLES:   # a pack's accented off-beat stab is its groove
            fails.append("%s: off-beats as loud as downbeats" % role)
        if role == "bass" and cells_used:
            allowed = {(b, st) for b, name in cells_used.items() for st, *_ in CELLS[name]} | {(b, 14) for b in cells_used}
            stray = [s for s, *_ in notes if (int(s // 4), int(round((s % 4) * 4))) not in allowed]
            r["stray_starts"] = len(stray)
            if stray:
                fails.append("bass: %d starts outside its cells" % len(stray))
        if role == "answer":
            clash = 0
            for s, d, *_ in notes:
                for i in range(int(s * 4), int(np.ceil((s + d) * 4))):
                    if i < len(vmap["sung"]) and vmap["sung"][i]:
                        clash += 1
                        break
            r["notes_while_she_sings"] = clash
            if clash:
                fails.append("answer: %d notes while she sings" % clash)
        out[role] = r
    return {"parts": out, "fails": fails, "ok": not fails}


def section_cells(sections: list[dict], bars: int) -> dict[int, str]:
    """Bar -> bass cell from sections [{"bars": [first, end), "cell": name, "last": {"bars": n, "cell": name}}] (0-based, end exclusive);
    "last" swaps the cell for the section's last n bars (a lift into the next one)."""
    out = {}
    for s in sections:
        a, z = s["bars"]
        for b in range(a, min(z, bars)):
            out[b] = s.get("cell")
        if s.get("last"):
            for b in range(max(a, z - int(s["last"]["bars"])), min(z, bars)):
                out[b] = s["last"]["cell"]
    return {b: c for b, c in out.items() if c in CELLS}


def arrange(chords: list[dict], bars: int, vmap: dict, voice: tuple[int, int], key_pc: int, mode: str, sections: list[dict],
            answer_every: int = 2, soft_bars: tuple = ()) -> dict:
    """All four parts and their check: keys and pad from the phrase modes, bass from the sections' cells, the answer line in her rests.
    soft_bars (0-based) play at 75 % velocity (a whispered or quiet passage)."""
    modes = phrase_modes(vmap, bars)
    kp = keys_parts(chords, bars, modes, voice)
    cells = section_cells(sections, bars)
    bass = bass_part(chords, bars, cells.get, key_pc, mode)
    ans, used = answer_part(chords, bars, vmap, voice, key_pc, mode, every=answer_every)
    parts = {"pad": kp["pad"], "keys": kp["keys"], "bass": bass, "answer": ans}
    soft = set(soft_bars)
    parts = {k: [(s, d, p, max(1, int(v * 0.75)) if int(s // 4) in soft else v) for s, d, p, v in ns] for k, ns in parts.items()}
    return {"parts": parts, "modes": modes, "cells": cells, "answers": used, "check": check(parts, vmap, cells)}


# ---------------------------------------------------------------- in a remix: the vocal on the remix grid, and the pass over a pack's parts

SECTION_CELLS = {"intro": "whole", "verse": "halves", "groove": "halves", "pre": "quarters", "build": "quarters", "chorus": "push", "drop": "push",
                 "hook": "anticipate", "break": "whole", "bridge": "halves_fifth", "outro": "whole", "tag": "whole"}
LIMITS.update({"stab": {"poly": 4, "per_bar": 32, "grid": 0.25}, "arp": {"poly": 2, "per_bar": 32, "grid": 0.25},
               "reese": {"poly": 2, "per_bar": 32, "grid": 0.25}, "sub": {"poly": 1, "per_bar": 32, "grid": 0.25}})


def file_spans(clips: list, tpb: int, ratio: float, fl_stretch: bool) -> list[tuple[float, float, float, float]]:
    """The vocal's playlist clips (position and length in ticks, the content window in ms, remixbuild._vocal_clips) as (start beat, beats,
    file second at the start, file seconds per remix second): 1 for a file stretched to the remix tempo, the stretch ratio when FL stretches
    a file left at its own speed."""
    return [(pos / tpb, length / tpb, w0 / 1000.0, ratio if fl_stretch else 1.0) for pos, length, w0, _w1 in clips]


def _beat_of(t: float, span: tuple, bpm: float) -> float | None:
    pos, n, t0, speed = span
    b = pos + (t - t0) / speed * bpm / 60.0
    return b if pos - 1e-6 <= b <= pos + n + 1e-6 else None


def remix_vocal_map(x: np.ndarray, rate: int, spans: list, bpm: float, beats: int, floor_under_db: float = 20.0) -> dict:
    """Where she sings on the remix grid: the vocal file's envelope read through the clips that place it (a 16th is sung when a third of it
    is above the floor), and her onsets mapped the same way. The default floor is 20 dB under the loud level: separated stems carry bleed."""
    mono = np.asarray(x, float).mean(axis=1) if np.ndim(x) == 2 else np.asarray(x, float)
    env = vocalchunk.envelope(mono, rate)
    floor = vocalchunk.floor_of(env, floor_under_db)
    on, win = env > floor, vocalchunk.WIN_S
    sung = [False] * (beats * 4)
    for pos, n, t0, speed in spans:
        for i in range(max(0, int(np.ceil(pos * 4))), min(len(sung), int((pos + n) * 4))):
            a = t0 + (i / 4 - pos) * 60.0 / bpm * speed
            seg = on[max(0, int(a / win)):max(0, int((a + 15.0 / bpm * speed) / win))]
            sung[i] = sung[i] or (len(seg) > 0 and float(np.mean(seg)) >= 0.34)
    ons = []
    for t0, t1 in vocalchunk.voiced_runs(env, floor, win):
        if t1 - t0 >= 0.06:
            ons += vocalchops.onsets(mono, rate, max(0.0, t0 - 0.02), t1, 0.09) or [t0]
    beats_on = sorted({round(b, 3) for t in ons for sp in spans for b in [_beat_of(t, sp, bpm)] if b is not None})
    return {"sung": sung, "onsets": beats_on, "floor_db": round(floor, 1)}


def remix_pitch_notes(x: np.ndarray, rate: int, spans: list, bpm: float, min_s: float = 0.08) -> list[tuple]:
    """Her line as notes on the remix grid, for her range and for a guide melody only (never played as sung): YIN every 20 ms, a note where
    the pitch holds within 60 cents for min_s, its median pitch rounded; start and length on 16ths."""
    from . import wavetables
    mono = np.asarray(x, float).mean(axis=1) if np.ndim(x) == 2 else np.asarray(x, float)
    times, f0 = wavetables.f0_track(mono, rate, 80.0, 1100.0, 0.02)
    notes, cur = [], []
    for t, f in list(zip(times, f0)) + [(times[-1] + 1 if len(times) else 0.0, np.nan)]:
        m = 69 + 12 * np.log2(f / 440.0) if np.isfinite(f) else None
        if m is not None and cur and abs(m - np.median([c[1] for c in cur])) <= 0.6:
            cur.append((t, m))
            continue
        if len(cur) > 1 and cur[-1][0] - cur[0][0] >= min_s:
            notes.append((cur[0][0], cur[-1][0] + 0.02, int(round(float(np.median([c[1] for c in cur]))))))
        cur = [(t, m)] if m is not None else []
    out = []
    for a, z, k in notes:
        for sp in spans:
            b0, b1 = _beat_of(a, sp, bpm), _beat_of(z, sp, bpm)
            if b0 is not None and b1 is not None:
                s = round(b0 * 4) / 4
                out.append((s, max(0.25, round(b1 * 4) / 4 - s), k, 90))
    return sorted(out)


def _bars(notes: list) -> dict[int, list]:
    out: dict[int, list] = {}
    for n in notes:
        out.setdefault(int(n[0] // 4), []).append(n)
    return out


def _curve(notes: list, role: str) -> list[tuple]:
    """Beat-strength velocities for a part whose velocities are flat (spread under 5), at the part's own average loudness."""
    if not notes:
        return []
    v = np.array([n[3] for n in notes], float)
    if len(v) < 4 or v.std() >= 5:
        return [tuple(n) for n in notes]
    scale = float(v.mean()) / 96.0
    return [(n[0], n[1], n[2], velocity(n[0], scale, role)) + tuple(n[4:]) for n in notes]


def fit_part(role: str, notes: list, vmap: dict, voice: tuple[int, int], bars: int) -> list[tuple]:
    """A style pack's part made to give the singer room (the session-arranger rules over a genre's own patterns): the arp only where she
    rests or her phrase is spacious (call and response); the stabs held as one legato chord per bar under a busy phrase; stab and pad
    notes inside her range moved an octave down (not under C3); at most four notes struck at once; flat velocities given a beat curve.
    Bass lines keep their pack pattern (already a deliberate cell) and only get the velocity curve."""
    if not notes:
        return []
    mode_of = {b: m["mode"] for m in phrase_modes(vmap, bars) for b in range(*m["bars"])}
    sung = vmap["sung"]

    def over_voice(s: float, d: float) -> bool:
        return any(i < len(sung) and sung[i] for i in range(int(s * 4), int(np.ceil((s + d) * 4))))
    out = [tuple(n) for n in notes]
    if role == "arp":
        out = [n for n in out if mode_of.get(int(n[0] // 4)) == "move" or not over_voice(n[0], n[1])]
    if role == "stab":
        held = []
        for b, ns in sorted(_bars(out).items()):
            if mode_of.get(b) != "hold":
                held += ns
                continue
            first = min(n[0] for n in ns)
            keys = sorted({n[2] for n in ns if abs(n[0] - first) < 1e-6})
            held += [(b * 4.0, 3.95, k, velocity(b * 4.0, 0.8, "stab")) for k in keys]
        out = held
    if role in ("stab", "pad"):
        lo, hi = voice[0] - 1, voice[1] + 2
        out = [(n[0], n[1], n[2] - 12 if lo <= n[2] <= hi and n[2] - 12 >= 48 else n[2], *n[3:]) for n in out]
        by_start: dict[float, list] = {}
        for n in out:
            by_start.setdefault(round(n[0], 4), []).append(n)
        capped = []
        for _s, ns in sorted(by_start.items()):
            ns = sorted(set(ns), key=lambda n: n[2])
            capped += ns if len(ns) <= 4 else [ns[0], ns[1], ns[-2], ns[-1]]
        out = capped
    return sorted(_curve(out, role))


def remix_support(sup: dict, vmap: dict, pitch: list, chords: list[dict], sections: list[dict], bars: int, key_pc: int, mode: str) -> dict:
    """What the support pass needs once per build: her map and range, the guide (when sup asks for one), the answer line, and the parts
    the arranger writes when sup's parts_from is "arranger" (the bass cell of each remix section from SECTION_CELLS)."""
    voice = voice_range(pitch)
    st = {"vmap": vmap, "voice": voice, "guide": guide_melody(pitch, key_pc, mode) if sup.get("guide") else [],
          "answer": answer_part(chords, bars, vmap, voice, key_pc, mode, every=int(sup.get("answer_every", 2)))[0], "written": None}
    if sup.get("parts_from") == "arranger":
        secs = [{"name": s["name"], "bars": [s["start"], s["end"]], "cell": SECTION_CELLS.get(s["name"].split("_")[0], "halves")} for s in sections]
        st["written"] = arrange(chords, bars, vmap, voice, key_pc, mode, secs, int(sup.get("answer_every", 2)))["parts"]
    return st


def apply_support(role: str, notes: list, st: dict | None, bars: int) -> list[tuple]:
    """One part through the support pass (roles as the remix build names them: reese, sub, stab, arp, pad). The arranger's own parts when it
    wrote them (stab plays the keys figure, reese the bass, arp the answer line, no sub); else the pack's part fitted. The arp channel also
    carries the answer line where the pack's arp is silent, and the guide melody when one was asked for."""
    if st is None:
        return [tuple(n) for n in notes]
    w = st.get("written")
    if w is not None:
        # the bass sampler plays its sample's own pitch on key 60 (st["bass_root"], A1 for the styles' samples): true pitch is midi + 60 - root
        bass = [(n[0], n[1], n[2] + 60 - int(st.get("bass_root", 33)), n[3]) for n in w["bass"]]
        got = {"stab": w["keys"], "pad": w["pad"], "reese": bass, "sub": [], "arp": w["answer"]}.get(role, notes)
    else:
        got = fit_part(role, notes, st["vmap"], st["voice"], bars)
        if role == "arp":
            busy = set(_bars(got))
            got = got + [n for n in st["answer"] if int(n[0] // 4) not in busy]
    if role == "arp" and st.get("guide"):
        got = list(got) + list(st["guide"])
    return sorted(tuple(n) for n in got)


def with_original(plan: dict) -> int:
    """Her own instruments under the arranged parts (the person's options 2 and 4, 2026-11-06): every sung clip of the plan gets the "other"
    stem over the same span, unless one is already there. Edits plan in place; returns how many clips it added."""
    clips, words = plan["vocal_clips"], plan["clip_words"]
    have = {(int(c[0]), round(float(c[2]), 2)) for c in clips if len(c) > 6 and c[6] == "other"}
    add = []
    for c in clips:
        if (len(c) < 7 or c[6] == "vocals") and (int(c[0]), round(float(c[2]), 2)) not in have:
            add.append([c[0], c[1], c[2], c[3], "%s (her instruments)" % c[4], "bars", "other"])
    for c in add:
        clips.append(c)
        words.append({"head": "", "tail": ""})
    return len(add)
