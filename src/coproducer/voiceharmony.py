"""The vocal as the guide: its notes (a pitch editor's MIDI, such as Newtone's "Save as MIDI") placed on the remix grid, a chord loop chosen
to fit them, and a lead line that doubles them in key.

The person (2026-10-29): remake the synths and the bass "based on the vocals ... use them as your guide for the tone", with the voice, the
synth, the bass and the stabs "all in musical key together". The record's own chords are dropped (the plan re-harmonizes): the loop that
best holds the voice's notes, bar by bar, plays under the whole song, and the lead synth plays the tuned voice's own notes snapped to the key.
"""
from __future__ import annotations

from collections import defaultdict

MINOR = (0, 2, 3, 5, 7, 8, 10)
MAJOR = (0, 2, 4, 5, 7, 9, 11)
# four-chord loops, as (semitones over the tonic, quality); sources: the common pop and dance loops in each mode
LOOPS = {
    "minor": {
        "i-VI-III-VII": ((0, "min"), (8, "maj"), (3, "maj"), (10, "maj")),
        "VI-III-VII-i": ((8, "maj"), (3, "maj"), (10, "maj"), (0, "min")),
        "i-iv-VI-V": ((0, "min"), (5, "min"), (8, "maj"), (7, "maj")),
        "i-VII-VI-VII": ((0, "min"), (10, "maj"), (8, "maj"), (10, "maj")),
        "i-v-VI-iv": ((0, "min"), (7, "min"), (8, "maj"), (5, "min")),
        "VI-VII-i-i": ((8, "maj"), (10, "maj"), (0, "min"), (0, "min")),
    },
    "major": {
        "I-V-vi-IV": ((0, "maj"), (7, "maj"), (9, "min"), (5, "maj")),
        "vi-IV-I-V": ((9, "min"), (5, "maj"), (0, "maj"), (7, "maj")),
        "I-vi-IV-V": ((0, "maj"), (9, "min"), (5, "maj"), (7, "maj")),
        "IV-V-iii-vi": ((5, "maj"), (7, "maj"), (4, "min"), (9, "min")),
    },
}


def midi_notes(path: str) -> list[dict]:
    """[{start_s, end_s, pitch, velocity}] from a MIDI file, in seconds (the file's own tempo map)."""
    import mido
    t, on, out = 0.0, {}, []
    for msg in mido.MidiFile(path):
        t += msg.time
        if msg.type == "note_on" and msg.velocity > 0:
            on[(msg.channel, msg.note)] = (t, msg.velocity)
        elif msg.type in ("note_off", "note_on") and (msg.channel, msg.note) in on:
            t0, v = on.pop((msg.channel, msg.note))
            if t > t0:
                out.append({"start_s": round(t0, 4), "end_s": round(t, 4), "pitch": msg.note, "velocity": v})
    return sorted(out, key=lambda n: n["start_s"])


def key_profile(notes: list[dict]) -> list[float]:
    """Seconds sung on each pitch class."""
    pc = [0.0] * 12
    for n in notes:
        pc[n["pitch"] % 12] += n["end_s"] - n["start_s"]
    return pc


def to_remix(notes: list[dict], clips: list[list], origin_s: float, source_bpm: float, shift_s: float = 0.0, only=None) -> list[tuple]:
    """(remix beat, beats, pitch, velocity) for each note inside a plan vocal clip [remix_bar, source_bar, start_s, end_s, label, mode, stem]
    (the vocal plays at its own tempo on the remix grid: one source beat is one remix beat). shift_s moves the MIDI's clock onto the stem's
    (a padded file's padding). only: labels to keep (all vocal clips when None)."""
    beat = 60.0 / source_bpm
    out = []
    for c in clips:
        if (c[6] if len(c) > 6 else "vocals") != "vocals" or (only is not None and c[4] not in only):
            continue
        r_bar, s_bar, a, b = c[0], c[1], c[2], c[3]
        for n in notes:
            t0, t1 = n["start_s"] - shift_s, n["end_s"] - shift_s
            if t0 < a or t0 >= b:
                continue
            pos = r_bar * 4 + (t0 - origin_s) / beat - s_bar * 4
            out.append((round(pos, 4), round(max(0.05, min(t1, b) - t0) / beat, 4), n["pitch"], n["velocity"]))
    return sorted(out)


def weights_by_bar(rows: list[tuple]) -> dict[int, list[float]]:
    """Beats sung per pitch class in each remix bar."""
    w: dict[int, list[float]] = defaultdict(lambda: [0.0] * 12)
    for pos, dur, pitch, _v in rows:
        w[int(pos // 4)][pitch % 12] += dur
    return dict(w)


def _fit(weights: list[float], root: int, quality: str, scale: set[int]) -> float:
    third = 3 if quality == "min" else 4
    tones = {root % 12, (root + third) % 12, (root + 7) % 12}
    color = {(root + 10) % 12 if quality == "min" else (root + 11) % 12, (root + 2) % 12}
    s = 0.0
    for pc, w in enumerate(weights):
        if pc in tones:
            s += w
        elif pc in color and pc in scale:
            s += 0.5 * w
        elif any((pc - t) % 12 == 1 for t in tones) or pc not in scale:   # a semitone over a chord tone, or outside the key: it clashes
            s -= w
    return s


def best_loop(weights: dict[int, list[float]], key_pc: int, mode: str = "minor", bars_per_chord=(1, 2)) -> dict:
    """The four-chord loop, chord length and phase that hold the voice's notes best over every sung bar. Returns {name, bars_per_chord,
    phase, score, roots8, qualities ({pc: quality}), per_chord, alternatives}."""
    scale = {(key_pc + s) % 12 for s in (MINOR if mode == "minor" else MAJOR)}
    rows = []
    for name, loop in LOOPS[mode].items():
        for bpc in bars_per_chord:
            span = 4 * bpc
            for phase in range(span):
                score = 0.0
                for bar, w in weights.items():
                    deg, q = loop[((bar + phase) % span) // bpc]
                    score += _fit(w, key_pc + deg, q, scale)
                rows.append((round(score, 3), name, bpc, phase))
    rows.sort(key=lambda r: -r[0])
    score, name, bpc, phase = rows[0]
    loop = LOOPS[mode][name]
    span = 4 * bpc
    roots8 = [(key_pc + loop[((b + phase) % span) // bpc][0]) % 12 for b in range(8)]
    quals = {(key_pc + d) % 12: q for d, q in loop}
    return {"name": name, "bars_per_chord": bpc, "phase": phase, "score": score, "roots8": roots8, "qualities": quals,
            "alternatives": [{"name": n, "bars_per_chord": c, "phase": p, "score": s} for s, n, c, p in rows[1:6]]}


def snap(pitch: int, key_pc: int, mode: str = "minor") -> int:
    """The nearest pitch in the key (down on a tie)."""
    scale = {(key_pc + s) % 12 for s in (MINOR if mode == "minor" else MAJOR)}
    for d in (0, -1, 1, -2, 2):
        if (pitch + d) % 12 in scale:
            return pitch + d
    return pitch


def lead_rows(rows: list[tuple], key_pc: int, mode: str = "minor", low: int = 60, high: int = 84, min_beats: float = 0.12) -> list[tuple]:
    """The voice's notes as a lead synth line: snapped to the key, moved by octaves into low..high, too-short blips dropped."""
    out = []
    for pos, dur, pitch, vel in rows:
        if dur < min_beats:
            continue
        p = snap(pitch, key_pc, mode)
        while p < low:
            p += 12
        while p > high:
            p -= 12
        out.append((pos, dur, p, max(60, min(118, int(vel)))))
    return out


# ---- chords per section, from the voice (the person, 2026-10-29: "I want the synth to follow the chord progressions of the vocals")

DIATONIC = {"minor": {0: "min", 3: "maj", 5: "min", 7: "min", 8: "maj", 10: "maj"},   # i III iv v VI VII (the diminished ii left out)
            "major": {0: "maj", 2: "min", 4: "min", 5: "maj", 7: "maj", 9: "min"}}   # I ii iii IV V vi (the diminished vii left out)
MOTION = {5: 1.0, 7: 0.6, 8: 0.6, 9: 0.6, 3: 0.4, 4: 0.4, 2: 0.4, 10: 0.4, 1: 0.2, 11: 0.2, 6: -0.5}   # root motion (semitones up) -> how strong
CHORD_BARS = {"build": 1}   # bars a chord in each section kind; 2 elsewhere (a pre-chorus pushes with a chord a bar)


def _kind_rows(weights: dict[int, list[float]], sections: list[dict]) -> dict[str, list[tuple[int, list[float]]]]:
    rows: dict[str, list[tuple[int, list[float]]]] = defaultdict(list)
    for s in sections:
        for b in range(s["start"], s["end"]):
            if b in weights:
                rows[s["name"]].append((b - s["start"], weights[b]))
    return dict(rows)


def _best_four(rows, qual: dict[int, str], scale: set[int], bpc: int, key_pc: int) -> tuple[float, tuple[int, ...], float]:
    """The four chords (roots, looping) that hold these bars' sung notes best, with a small reward for strong root motion and the tonic.
    Returns (score, roots, fit: the notes' part of the score)."""
    from itertools import product
    beats = sum(sum(w) for _r, w in rows) / max(1, len({r for r, _w in rows}))
    best = (-1e9, (), 0.0)
    for seq in product(sorted(qual), repeat=4):
        if any(seq[i] == seq[(i + 1) % 4] for i in range(4)):
            continue
        fit = sum(_fit(w, seq[(rel // bpc) % 4], qual[seq[(rel // bpc) % 4]], scale) for rel, w in rows)
        bonus = sum(MOTION.get((seq[(i + 1) % 4] - seq[i]) % 12, 0.0) for i in range(4)) + (1.0 if key_pc in seq else 0.0)
        score = fit + 0.15 * beats * bonus
        if score > best[0]:
            best = (round(score, 3), seq, round(fit, 3))
    return best


def section_loops(weights: dict[int, list[float]], sections: list[dict], key_pc: int, mode: str = "minor", qualities=None,
                  min_beats: float = 4.0, min_fit: float = 0.3) -> dict:
    """Chords that follow the voice section by section: per section kind (verse grooves, pre-chorus builds, chorus drops), the four-chord
    loop of the key's chords that holds the voice's notes in that kind's bars best, a chord every CHORD_BARS bars from the section's start.
    Kinds the voice barely sings (under min_beats, or no loop holds min_fit of its sung beats) take the loop of the kind it sings most.
    qualities (pc: quality, such as V major in a minor key) override the key's own triads.
    Returns {bar_roots, qualities, kinds: {kind: {chords, bars_per_chord, score}}, borrowed_from}."""
    qual = {(key_pc + d) % 12: q for d, q in DIATONIC[mode].items()}
    qual.update({int(k): v for k, v in (qualities or {}).items() if int(k) in qual})
    scale = {(key_pc + s) % 12 for s in (MINOR if mode == "minor" else MAJOR)}
    rows = _kind_rows(weights, sections)
    sung = {k: v for k, v in rows.items() if sum(sum(w) for _r, w in v) >= min_beats}
    kinds = {}
    for kind, r in sung.items():
        bpc = CHORD_BARS.get(kind, 2)
        score, seq, fit = _best_four(r, qual, scale, bpc, key_pc)
        if fit >= min_fit * sum(sum(w) for _r, w in r):
            kinds[kind] = {"chords": list(seq), "bars_per_chord": bpc, "score": score}
    if not kinds:
        raise ValueError("the voice sings too little to choose chords from")
    lead = max(kinds, key=lambda k: sum(sum(w) for _r, w in sung[k]))
    roots = []
    for s in sections:
        k = kinds.get(s["name"]) or {**kinds[lead], "bars_per_chord": 2}
        roots += [k["chords"][((b - s["start"]) // k["bars_per_chord"]) % 4] for b in range(s["start"], s["end"])]
    used = set(roots)
    return {"bar_roots": roots, "qualities": {pc: q for pc, q in qual.items() if pc in used}, "kinds": kinds, "borrowed_from": lead}
