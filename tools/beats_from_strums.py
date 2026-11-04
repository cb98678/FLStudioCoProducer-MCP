"""The beats of a freely played recording (no click: an acoustic guitar and a voice) for tools/warp_to_grid.py, from the strums.

    python tools/beats_from_strums.py --in OTHER_STEM.wav --out beats.json [--bpm 117] [--lo 90 --hi 150] [--refine-ms 70]

A beat tracker (dynamic programming over the onset strength of the harmony stem, Ellis 2007, pulled toward --bpm or the stem's own
autocorrelation estimate within --lo..--hi) gives the pulse; each beat then moves to the start of the nearest strum within --refine-ms: the point where
the onset strength first rises past a fifth of its peak, not the peak (on Hello Toni the peaks sat 25 to 30 ms after the strums' true
starts, LESSONS row 128). Beats with no strum nearby keep the tracker's time and are listed in the report. Writes OUT (the beat times,
ascending) and OUT.report.json (tempo estimate, how many beats were refined, the spacing's spread, the tempo per 8 beats so a
ritardando shows). Inputs are only read; the output must sit under a folder named sandbox.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


def strum_starts(env: np.ndarray, peak_i: int, share: float = 0.2, reach: int = 12) -> int:
    """The frame where the onset strength first rises past `share` of the peak, looking back up to `reach` frames."""
    top = env[peak_i]
    i = peak_i
    while i > 0 and peak_i - i < reach and env[i - 1] >= share * top and env[i - 1] <= env[i] + 1e-9:
        i -= 1
    return i


def tempo_estimate(env: np.ndarray, fps: float, lo: float, hi: float) -> float:
    """The tempo in lo..hi whose period the onset strength's autocorrelation likes best."""
    e = env - env.mean()
    ac = np.correlate(e, e, mode="full")[len(e) - 1:]
    lags = np.arange(int(fps * 60.0 / hi), int(fps * 60.0 / lo) + 1)
    k = lags[int(np.argmax(ac[lags]))]
    return 60.0 * fps / k


def track_beats(env: np.ndarray, fps: float, bpm: float, tightness: float = 100.0) -> np.ndarray:
    """Dynamic-programming beat tracking (Ellis 2007): beats where the onset strength is high and the spacing stays near 60/bpm, the
    penalty tightness * log(spacing / period)^2 letting the pulse follow a drift."""
    period = fps * 60.0 / bpm
    n = len(env)
    e = env / (env.max() + 1e-12)
    score = np.zeros(n)
    back = np.full(n, -1, dtype=int)
    lo, hi = int(round(period * 0.5)), int(round(period * 2.0))
    for i in range(n):
        j0, j1 = i - hi, i - lo
        if j1 < 0:
            score[i] = e[i]
            continue
        j0 = max(0, j0)
        js = np.arange(j0, j1 + 1)
        pen = -tightness * np.log((i - js) / period) ** 2
        cand = score[j0:j1 + 1] + pen
        k = int(np.argmax(cand))
        score[i] = e[i] + cand[k]
        back[i] = js[k]
    # start from the best score in the last period and walk back
    tail = max(0, n - int(period))
    i = tail + int(np.argmax(score[tail:]))
    beats = []
    while i >= 0:
        beats.append(i)
        i = back[i]
    return np.asarray(beats[::-1], dtype=int)


def refine(beats_f: np.ndarray, env: np.ndarray, reach_f: int) -> tuple[list[int], list[bool]]:
    out, moved = [], []
    for b in beats_f:
        lo, hi = max(0, b - reach_f), min(len(env) - 1, b + reach_f)
        seg = env[lo:hi + 1]
        if not len(seg) or seg.max() < 0.25 * np.percentile(env, 90):
            out.append(int(b)); moved.append(False)
            continue
        p = lo + int(np.argmax(seg))
        out.append(strum_starts(env, p)); moved.append(True)
    return out, moved


def keep_spacing(tracked: list[int], refined: list[int], moved: list[bool], period: float, lo: float = 0.78, hi: float = 1.25) -> tuple[list[int], list[bool]]:
    """A refinement that lands under lo or over hi periods from its neighbours (a syncopated strum next to the beat) goes back to the
    tracker's time; the neighbour before is the accepted one, the one after the tracker's."""
    out, kept = [], []
    for i, (t, r, m) in enumerate(zip(tracked, refined, moved)):
        ok = m
        if m and i > 0 and not lo * period <= r - out[-1] <= hi * period:
            ok = False
        if m and i + 1 < len(tracked) and not lo * period <= tracked[i + 1] - r <= hi * period:
            ok = False
        out.append(r if ok else t)
        kept.append(ok)
    return out, kept


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--bpm", type=float, default=0.0, help="a tempo to pull the tracker toward (0: the stem's own estimate)")
    ap.add_argument("--lo", type=float, default=80.0)
    ap.add_argument("--hi", type=float, default=160.0)
    ap.add_argument("--refine-ms", type=float, default=70.0)
    a = ap.parse_args()
    out = Path(a.out)
    if "sandbox" not in out.resolve().parts:
        print("the output must sit under a folder named sandbox", file=sys.stderr)
        return 2
    import soundfile as sf

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from coproducer import newtimeview

    x, rate = sf.read(a.src, dtype="float64", always_2d=True)
    y = x.mean(axis=1)
    hop = 256
    env = newtimeview.onset_envelope(y, rate, hop=hop)
    fps = rate / hop
    tempo = a.bpm or tempo_estimate(env, fps, a.lo, a.hi)
    tempo = min(max(tempo, a.lo), a.hi)
    beats_f = track_beats(env, fps, tempo)
    reach_f = int(round(a.refine_ms / 1000.0 * rate / hop))
    frames, moved = refine(beats_f, env, reach_f)
    frames, moved = keep_spacing(list(beats_f), frames, moved, fps * 60.0 / tempo)
    times = sorted(set(round(float(f * hop / rate), 4) for f in frames))
    d = np.diff(times)
    per8 = [round(60.0 / float(np.mean(d[i:i + 8])), 2) for i in range(0, len(d) - 7, 8)] if len(d) >= 8 else []
    rep = {"source": a.src, "tempo_estimate": round(tempo, 2), "beats": len(times), "refined": int(sum(moved)), "unrefined_beats": [round(float(beats_f[i] * hop / rate), 3) for i, m in enumerate(moved) if not m],
           "spacing_s": {"median": round(float(np.median(d)), 4), "min": round(float(d.min()), 4), "max": round(float(d.max()), 4)} if len(d) else {},
           "bpm_per_8_beats": per8, "first_beat_s": times[0] if times else None}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(times), encoding="utf-8")
    out.with_name(out.stem + ".report.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
    print(json.dumps(rep, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
