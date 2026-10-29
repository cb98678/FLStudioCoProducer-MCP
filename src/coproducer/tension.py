"""Piano-roll note generators for tension: pedal swells, gated subs, a held bar before the drop, rising arps, kick-aware truncation.

Notes are (start_beat, duration_beats, key, velocity) with key as FL's raw piano-roll number (MIDI minus 12). Which
sound a raw key makes depends on the patch (the Deep Sytrus patch applies -19 semitones); check by rendering.
"""
from __future__ import annotations

Note = tuple[float, float, int, int]
BAR_BEATS = 4


def pedal_swell(bar: int, bars: int, key: int, v0: int = 82, ramp: int = 12, octave_key: int | None = None, octave_from: int = 2) -> list[Note]:
    """One long note per bar rising in velocity; an octave layer joins from bar octave_from of the run."""
    out: list[Note] = []
    for k in range(bars):
        out.append(((bar + k) * BAR_BEATS, 3.9, key, v0 + ramp * k))
        if octave_key is not None and k >= octave_from:
            out.append(((bar + k) * BAR_BEATS, 3.9, octave_key, 72 + 16 * (k - octave_from)))
    return out


def gated_sub(bar: int, key: int, steps: tuple[int, ...] = (2, 6, 10, 14), vel: int = 96, dur: float = 0.45) -> list[Note]:
    """Short stabs on 16th-grid steps of one bar."""
    return [((bar * 16 + s) / 4, dur, key, vel) for s in steps]


def sixteenth_gate(bar: int, key: int, v0: int = 100) -> list[Note]:
    """Off-beat 16ths with velocity climbing across the bar."""
    return [((bar * 16 + s) / 4, 0.2, key, v0 + s) for s in range(1, 16, 2)]


def hold_before_drop(bar: int, key: int, octave_key: int, beats: float = 3.0) -> list[Note]:
    """A held low note for most of the last build bar, then an octave-up pickup into the drop."""
    return [(bar * BAR_BEATS, beats, key, 115), (bar * BAR_BEATS + beats, 0.5, octave_key, 100)]


def drop_accent(bar: int, octave_key: int) -> list[Note]:
    return [(bar * BAR_BEATS + 0.5, 1.5, octave_key, 95)]


def rising_arp(bar: int, chords: list[list[int]], v0: int = 48, bar_ramp: int = 14, step_ramp: float = 2.5, dur: float = 0.22) -> list[Note]:
    """16th arpeggio over one chord per bar, each bar louder than the last."""
    out: list[Note] = []
    for i, keys in enumerate(chords):
        for s in range(16):
            out.append((((bar + i) * 16 + s) / 4, dur, keys[s % len(keys)], int(v0 + i * bar_ramp + s * step_ramp)))
    return out


def truncate_at_kicks(notes: list[Note], kick_beats: list[float], gap: float = 0.04, min_len: float = 0.15) -> list[Note]:
    """Cut each note where the next kick lands (sidechain-free ducking by gating); drop notes that become shorter than min_len."""
    ks = sorted(kick_beats)
    out: list[Note] = []
    for st, d, key, vel in notes:
        nxt = next((k for k in ks if k > st + 1e-6), 1e9)
        nd = min(d, nxt - st - gap)
        if nd >= min_len:
            out.append((st, nd, key, vel))
    return out


def shift_beats(notes: list[Note], beats: float) -> list[Note]:
    """Shift notes in time; notes pushed before beat 0 are dropped. Used to align generated audio's timing to the project grid."""
    return [(s + beats, d, k, v) for s, d, k, v in notes if s + beats >= 0]


def drop_build(break_bar: int, break_bars: int, build_bar: int, build_bars: int, root: int, octave: int, arp_chords: list[list[int]]) -> tuple[list[Note], list[Note]]:
    """Bass notes and arp notes for a break plus a build: swell, gated stabs, 16th gate, hold, drop accent. Returns (bass, arp)."""
    bass = pedal_swell(break_bar, break_bars, root, octave_key=octave)
    last = build_bar + build_bars - 1
    for b in range(build_bar, last):
        bass += gated_sub(b, root, vel=96 + 8 * (b - build_bar)) if b < last - 1 else sixteenth_gate(b, root)
    bass += hold_before_drop(last, root, octave)
    bass += drop_accent(last + 1, octave)
    return bass, rising_arp(build_bar, arp_chords)
