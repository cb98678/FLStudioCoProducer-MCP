"""Cut a long vocal into phrase chunks before Newtime and Newtone (skill vocal-chunking).

The person (2026-11-03): "when dealing with vocals that are long because we rip them from an entire song we should consider splitting
them up into chunks that align with the phrasing and syllables, so that when we Newtime and Newtone them they are easier to work with and
fall correctly on beat without major stretches to long vocal files. The slicing should be very careful to evaluate the syllables'
beginnings and ends and ensure we are clipping them correctly."

What a chunk is here: one sung phrase (or a few, up to `max_beats`), cut only where the voice is silent, carried through its last word's
release, never through a syllable, and written as a file that starts on a line of the song's grid (a beat when the silence allows it, a
16th otherwise) so that Newtime's grid, which starts at the file's start, is the project's grid, and the chunk's playlist position is a
whole number of 16ths. Rules, measured on sung voices (vocalchops, cutrefine):

* the voice is sounding where the 10 ms RMS envelope is above the floor: `floor_under_db` (30 dB) under the file's loud level (the 95th
  percentile of its sounding frames), so a quiet recording is read like a loud one (breaths and bleed stay under it); a gap is a run of
  silent frames; a phrase gap is `phrase_gap_s` (0.25 s) or longer, a syllable gap `min_gap_s` (0.15 s, longer than a stop consonant's closure) or longer;
* a gap inside a word's span (the transcript's words, shrunk by `word_slack_s` at each end because a recogniser's times are loose) is a
  stop consonant's closure ("a-gainst", "ex-pect"), never a cut;
* the audio of a chunk starts `pre_s` (50 ms) before its first voiced frame and the chunk before it keeps `post_s` (60 ms) after its last
  voiced frame; when the gap is too short for both, the cut sits in its middle; every cut moves to a zero crossing and gets a 5 ms fade;
* the chunk's file starts on the latest grid line that lies in the gap at or before the cut (a beat if one does, else a 16th); when no
  grid line lies in the gap, the file starts on the latest 16th before the cut and is silent until the cut (so the file before it keeps
  its release and this one its attack; the two overlap only in digital silence);
* a chunk longer than `max_beats` is split at the longest syllable gaps inside it, outside words; one with less than `min_voiced_s` of
  voice is a breath or bleed and goes into the silence.

Everything is arithmetic over an envelope, onsets and word times, so the tests run on made-up audio; the files are written by
`write_chunks` and laid back on the song's clock by `assemble`.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from . import vocalchops

FLOOR_UNDER_DB = 30.0
PHRASE_GAP_S = 0.25
MIN_GAP_S = 0.15
WORD_SLACK_S = 0.06
PRE_S = 0.05
POST_S = 0.06
FADE_S = 0.005
MAX_BEATS = 16.0
MIN_VOICED_S = 0.12
WIN_S = 0.01


@dataclass
class Chunk:
    index: int
    grid_s: float          # where the chunk's file starts: a grid line of the song (seconds of the source file)
    grid_16ths: int        # that line as 16ths from the origin
    audio_s: float         # where its audio starts (the cut before its first syllable); the file is silent from grid_s to here
    end_s: float           # where its audio ends (the next cut)
    voiced: tuple[float, float] = (0.0, 0.0)   # first and last voiced frame
    on_beat: bool = True   # the file starts on a beat (else a 16th)
    padded: bool = False   # the file starts before the cut (silence first)
    words: list = field(default_factory=list)
    onsets: list = field(default_factory=list)
    offsets_ms: list = field(default_factory=list)
    flags: list = field(default_factory=list)
    file: str = ""


def envelope(mono: np.ndarray, rate: int, win_s: float = WIN_S) -> np.ndarray:
    return vocalchops.envelope_db(np.asarray(mono, dtype=float), rate, win_s)[0]


def floor_of(env_db: np.ndarray, under_db: float = FLOOR_UNDER_DB) -> float:
    """The silence floor: under_db below the 95th percentile of the frames that hold any sound."""
    live = env_db[env_db > -90.0]
    return float(np.percentile(live, 95) - under_db) if len(live) else -60.0


def voiced_runs(env_db: np.ndarray, floor_db: float, win_s: float) -> list[tuple[float, float]]:
    """(start, end) seconds of every run of frames above the floor."""
    on = env_db > floor_db
    out, start = [], None
    for i, v in enumerate(on):
        if v and start is None:
            start = i
        elif not v and start is not None:
            out.append((start * win_s, i * win_s))
            start = None
    if start is not None:
        out.append((start * win_s, len(on) * win_s))
    return out


def gaps_between(runs: list[tuple[float, float]]) -> list[tuple[float, float]]:
    return [(a[1], b[0]) for a, b in zip(runs, runs[1:])]


def inside_word(t0: float, t1: float, words: list[dict], slack: float = WORD_SLACK_S) -> dict | None:
    """The word whose (shrunk) span contains the gap (t0, t1): a closure inside it, not a boundary."""
    for w in words:
        if w["start"] + slack <= t0 and t1 <= w["end"] - slack and w["end"] - w["start"] > 2 * slack:
            return w
    return None


def phrase_runs(runs: list[tuple[float, float]], words: list[dict], phrase_gap_s: float = PHRASE_GAP_S, min_gap_s: float = MIN_GAP_S,
                min_voiced_s: float = MIN_VOICED_S, max_s: float = 1e9) -> list[tuple[float, float]]:
    """Join the voiced runs into phrases: a gap shorter than min_gap_s, or inside a word, joins; a phrase gap splits; a syllable gap splits
    only where the phrase would otherwise run past max_s (the longest such gaps first). Runs shorter than min_voiced_s on their own go."""
    runs = [r for r in runs if r[1] - r[0] > 0]
    if not runs:
        return []
    groups: list[list[tuple[float, float]]] = [[runs[0]]]
    for r in runs[1:]:
        gap = r[0] - groups[-1][-1][1]
        if gap >= phrase_gap_s and inside_word(groups[-1][-1][1], r[0], words) is None:
            groups.append([r])
        else:
            groups[-1].append(r)
    out = []
    for g in groups:
        out.extend(_split_long(g, words, min_gap_s, max_s))
    return [(g[0][0], g[-1][1]) for g in out if g[-1][1] - g[0][0] >= min_voiced_s]


def _split_long(g: list[tuple[float, float]], words: list[dict], min_gap_s: float, max_s: float) -> list[list[tuple[float, float]]]:
    if g[-1][1] - g[0][0] <= max_s or len(g) < 2:
        return [g]
    cands = [(b[0] - a[1], i) for i, (a, b) in enumerate(zip(g, g[1:])) if b[0] - a[1] >= min_gap_s and inside_word(a[1], b[0], words) is None]
    if not cands:
        return [g]
    _, i = max(cands)
    return _split_long(g[: i + 1], words, min_gap_s, max_s) + _split_long(g[i + 1:], words, min_gap_s, max_s)


def cut_point(gap: tuple[float, float], pre_s: float = PRE_S, post_s: float = POST_S) -> float:
    """Where the audio of the next phrase starts inside a gap: pre_s before its first voiced frame when the gap allows post_s after the last
    one of the phrase before, else the middle of the gap."""
    a, b = gap
    if b - a >= pre_s + post_s:
        return b - pre_s
    return (a + b) / 2.0


def grid_start(cut: float, gap: tuple[float, float], bpm: float, origin_s: float) -> tuple[float, int, bool, bool]:
    """The grid line the chunk's file starts on: (time, 16ths from the origin, on a beat, padded). The latest beat in [gap start, cut] when
    one lies there, else the latest 16th there, else the latest 16th before the cut with silence up to it."""
    step = 60.0 / bpm / 4.0
    lo = gap[0]
    k_cut = int(np.floor((cut - origin_s) / step + 1e-9))     # negative before the origin: the caller places it before bar 0
    k = k_cut
    while origin_s + k * step >= lo - 1e-9:
        if k % 4 == 0:
            t = origin_s + k * step
            return round(t, 6), k, True, bool(t < cut - 1e-6)
        k -= 1
    t = origin_s + k_cut * step
    return round(t, 6), k_cut, False, bool((t < cut - 1e-6) or (t < lo - 1e-9))


def zero_cross(mono: np.ndarray, rate: int, t: float, reach_s: float = 0.005) -> float:
    """The zero crossing nearest t within reach_s (t itself when there is none)."""
    i = int(round(t * rate))
    n = int(reach_s * rate)
    lo, hi = max(1, i - n), min(len(mono) - 1, i + n)
    if hi <= lo:
        return t
    seg = mono[lo - 1:hi + 1]
    cross = np.nonzero(np.signbit(seg[:-1]) != np.signbit(seg[1:]))[0]
    if not len(cross):
        return t
    j = cross[int(np.argmin(np.abs(cross + lo - i)))] + lo
    return float(j) / rate


def plan(mono: np.ndarray, rate: int, bpm: float, origin_s: float, words: list[dict] | None = None, onsets=None, floor_under_db: float = FLOOR_UNDER_DB,
         phrase_gap_s: float = PHRASE_GAP_S, min_gap_s: float = MIN_GAP_S, max_beats: float = MAX_BEATS, pre_s: float = PRE_S, post_s: float = POST_S,
         min_voiced_s: float = MIN_VOICED_S, max_move_s: float = 0.045) -> list[Chunk]:
    """The chunks of a vocal: where each file starts on the grid, where its audio starts and ends, its words, onsets and how far each onset
    sits from the nearest 16th (offsets_ms, negative early). Flags: long (over max_beats and no gap to split at), no_beat_line (the file
    starts on a 16th), padded (silence before the cut), off_grid (the median onset sits further than max_move_s from the 16ths: move the
    clip as a whole rather than stretch it), short (one voiced burst under 0.25 s)."""
    words = words or []
    env = envelope(mono, rate)
    runs = voiced_runs(env, floor_of(env, floor_under_db), WIN_S)
    beat = 60.0 / bpm
    phrases = phrase_runs(runs, words, phrase_gap_s, min_gap_s, min_voiced_s, max_beats * beat)
    if not phrases:
        return []
    dur = len(mono) / rate
    out: list[Chunk] = []
    prev_end = 0.0
    cuts = []
    for i, (v0, v1) in enumerate(phrases):
        gap = (prev_end, v0)
        c = cut_point(gap, pre_s, post_s) if i else max(0.0, v0 - pre_s)
        c = max(gap[0], min(c, v0))
        c = float(zero_cross(mono, rate, c))
        cuts.append((c, gap, (v0, v1)))
        prev_end = v1
    for i, (c, gap, (v0, v1)) in enumerate(cuts):
        end = cuts[i + 1][0] if i + 1 < len(cuts) else min(dur, v1 + post_s)
        g, k, on_beat, padded = grid_start(c, gap, bpm, origin_s)
        ch = Chunk(i, g, k, round(c, 6), round(end, 6), (round(v0, 3), round(v1, 3)), on_beat, padded)
        ch.words = [w["word"] for w in words if c <= (w["start"] + w["end"]) / 2.0 < end]   # a word's middle, since a recogniser's edges are loose
        if onsets is not None:
            step = beat / 4.0
            ons = [float(t) for t in np.asarray(onsets, dtype=float) if c <= t < end]
            ch.onsets = [round(t, 4) for t in ons]
            ch.offsets_ms = [round(1000.0 * ((t - origin_s) - round((t - origin_s) / step) * step), 1) for t in ons]
            if ons and abs(float(np.median(ch.offsets_ms))) > 1000.0 * max_move_s:
                ch.flags.append("off_grid")
        if (v1 - v0) > max_beats * beat + 1e-6:
            ch.flags.append("long")
        if not on_beat:
            ch.flags.append("no_beat_line")
        if padded:
            ch.flags.append("padded")
        if v1 - v0 < 0.25:
            ch.flags.append("short")
        out.append(ch)
    return out


def write_chunks(x: np.ndarray, rate: int, chunks: list[Chunk], folder, stem: str, fade_s: float = FADE_S, tail_s: float = 0.0) -> list[str]:
    """One WAV per chunk, named STEM_NN.wav: silence from its grid line to its cut, the audio to its end, 5 ms fades at both cuts, then
    tail_s of silence (two bars for Newtime: its view fits the file and its bar lines are read where the waveform is quiet, so a chunk
    that is voice from end to end showed fewer than two lines; the silence costs nothing, the join places files by their grid line)."""
    import soundfile as sf
    from pathlib import Path

    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    n_fade = max(1, int(fade_s * rate))
    for ch in chunks:
        i0, i1, g0 = int(round(ch.audio_s * rate)), int(round(ch.end_s * rate)), int(round(ch.grid_s * rate))
        seg = np.array(x[i0:i1], dtype=float)
        if len(seg) > 2 * n_fade:
            ramp = np.linspace(0.0, 1.0, n_fade)[:, None] if seg.ndim == 2 else np.linspace(0.0, 1.0, n_fade)
            seg[:n_fade] *= ramp
            seg[-n_fade:] *= ramp[::-1]
        pad, tail = max(0, i0 - g0), int(round(tail_s * rate))
        shape = lambda n: (n, seg.shape[1]) if seg.ndim == 2 else n   # noqa: E731
        p = folder / ("%s_%02d.wav" % (stem, ch.index))
        sf.write(str(p), np.concatenate([np.zeros(shape(pad)), seg, np.zeros(shape(tail))]), rate, subtype="PCM_24")
        ch.file = str(p)
        paths.append(str(p))
    return paths


def assemble(files: list[str], starts_s: list[float], rate: int, length_s: float, channels: int = 2) -> np.ndarray:
    """Lay chunk files back on one clock: each file starts at its start_s. Overlaps add (the files overlap only in digital silence)."""
    import soundfile as sf

    out = np.zeros((int(round(length_s * rate)), channels))
    for p, t in zip(files, starts_s):
        y, r = sf.read(p, dtype="float64", always_2d=True)
        if r != rate:
            raise ValueError("rate of %s is %d, not %d" % (p, r, rate))
        if y.shape[1] != channels:
            y = np.repeat(y.mean(axis=1, keepdims=True), channels, axis=1)
        i = int(round(t * rate))
        if i < 0:                       # a chunk whose grid line sits before the file's start (a pickup before beat 0)
            y, i = y[-i:], 0
        n = min(len(y), len(out) - i)
        if n > 0:
            out[i:i + n] += y[:n]
    return out


def manifest(chunks: list[Chunk], bpm: float, origin_s: float, source: str, lead_s: float, rate: int, duration_s: float, extra: dict | None = None) -> dict:
    return {"source": source, "bpm": bpm, "origin_s": origin_s, "lead_s": lead_s, "rate": rate, "duration_s": round(duration_s, 4),
            "chunks": [{"index": c.index, "file": c.file, "grid_s": c.grid_s, "grid_16ths": c.grid_16ths, "beat": round(c.grid_16ths / 4.0, 4),
                        "audio_s": c.audio_s, "end_s": c.end_s, "voiced_s": list(c.voiced), "on_beat": c.on_beat, "padded": c.padded,
                        "words": c.words, "text": " ".join(c.words), "onsets": c.onsets, "offsets_ms": c.offsets_ms,
                        "median_offset_ms": (round(float(np.median(c.offsets_ms)), 1) if c.offsets_ms else None), "flags": c.flags}
                       for c in chunks], **(extra or {})}
