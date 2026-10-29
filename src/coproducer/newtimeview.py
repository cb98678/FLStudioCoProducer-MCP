"""Warp markers for Newtime (FL Studio's time-warp editor) placed at a vocal's own syllable onsets, and reading Newtime's view from a screenshot
so each marker can be Shift+clicked at the right pixel.

Newtime's own Transient detection is built for drums ("peaks in the audio are used to estimate the beats"): on the Girlish vocal it left a
few markers per bar, mostly on note peaks, and Quantize time then moved almost nothing onto the grid (median onset offset 25 to 22 ms against
29 ms for random timing, 2026-10-29). Markers at the onsets themselves, then Quantize time at 1/4 beat, are what fits a vocal to the beat.

Sung onsets sit early: the energy rise of a syllable leads the beat it is sung on. On the Girlish vocal the strong onsets fitted a 16th grid
best 40 ms early (median 18 ms off there, 31 ms off the grid itself), so each marker goes at onset + lead_s and the singer keeps that lead
after quantizing. A marker is only placed when the move is small (max_move_s), when no closer onset wants the same grid line, and when the
stretch between neighbouring markers stays sane, so no syllable is pulled a whole 16th or squeezed.

The view reader finds the bar lines (the darkest grid columns, low colour) in a band of the editor above the waveform, which give pixels per
second exactly; the bar number comes from an approximate start (from the scroll handle) checked against the waveform's own shape.
"""
from __future__ import annotations

import numpy as np


def _frames(y: np.ndarray, n_fft: int, hop: int) -> np.ndarray:
    pad = np.concatenate([np.zeros(n_fft // 2), y, np.zeros(n_fft // 2)])
    n = 1 + (len(pad) - n_fft) // hop
    idx = np.arange(n_fft)[None, :] + hop * np.arange(n)[:, None]
    return pad[idx] * np.hanning(n_fft)[None, :]


def onset_envelope(y: np.ndarray, sr: int, hop: int = 128, n_fft: int = 2048, lag: int = 2) -> np.ndarray:
    """Spectral flux on log-compressed magnitudes with a 3-bin maximum filter (vibrato does not read as an onset), normalised to 0..1."""
    mags = np.abs(np.fft.rfft(_frames(np.asarray(y, dtype=float), n_fft, hop), axis=1))
    logm = np.log1p(100.0 * mags)
    ref = np.maximum(np.maximum(np.roll(logm, 1, axis=1), np.roll(logm, -1, axis=1)), logm)
    flux = np.zeros(len(logm))
    flux[lag:] = np.maximum(0.0, logm[lag:] - ref[:-lag]).mean(axis=1)
    lo, hi = flux.min(), flux.max()
    return (flux - lo) / (hi - lo) if hi > lo else flux * 0


def onset_times(y: np.ndarray, sr: int, hop: int = 128, delta: float = 0.15, wait_s: float = 0.09, floor_rms: float = 0.012) -> np.ndarray:
    """Onset times in seconds: envelope peaks that are the local maximum over 30 ms before, stand delta above the 100 ms mean around them,
    come wait_s after the last one, and start a sound louder than floor_rms (breaths and bleed stay unmarked)."""
    env = onset_envelope(y, sr, hop)
    fps = sr / hop
    pre_max, avg = max(1, int(0.03 * fps)), max(1, int(0.10 * fps))
    wait = int(wait_s * fps)
    y = np.asarray(y, dtype=float)
    out, last = [], -wait - 1
    for i in range(1, len(env) - 1):
        lo = max(0, i - pre_max)
        if env[i] < env[lo:i + 2].max() or env[i] <= 0:
            continue
        if env[i] < env[max(0, i - avg):i + avg + 1].mean() + delta or i - last <= wait:
            continue
        t = i * hop / sr
        seg = y[int(t * sr):int((t + 0.08) * sr)]
        if len(seg) and float(np.sqrt(np.mean(seg ** 2))) > floor_rms:
            out.append(t)
            last = i
    return np.asarray(out)


def best_lead(onsets, bpm: float, division: int = 4, max_lead_s: float = 0.09) -> float:
    """The lead (seconds, 5 ms steps) that puts the most onsets closest to the 1/division grid: how early this singer's onsets sit."""
    step = 60.0 / bpm / division
    t = np.asarray(onsets, dtype=float)
    if not len(t):
        return 0.0
    leads = np.arange(0.0, max_lead_s + 1e-9, 0.005)
    cost = [np.median(np.abs((t + L) - np.round((t + L) / step) * step)) for L in leads]
    return round(float(leads[int(np.argmin(cost))]), 3)


def warp_markers(onsets, bpm: float, lead_s: float = 0.04, max_move_s: float = 0.045, division: int = 4,
                 ratio: tuple[float, float] = (0.6, 1.7)) -> list[tuple[float, float]]:
    """(marker time, grid time) pairs: each onset + lead_s, moved to the nearest 1/division beat. One marker per grid line (the closest),
    moves above max_move_s skipped, and a marker dropped when the stretch from the previous kept marker leaves `ratio`."""
    step = 60.0 / bpm / division
    best: dict[int, tuple[float, float, float]] = {}
    for t in np.asarray(onsets, dtype=float) + lead_s:
        k = int(round(t / step))
        move = t - k * step
        if abs(move) <= max_move_s and (k not in best or abs(move) < abs(best[k][2])):
            best[k] = (float(t), k * step, move)
    kept: list[tuple[float, float]] = []
    for t, g, _ in sorted(best.values()):
        if kept:
            span, new = t - kept[-1][0], g - kept[-1][1]
            if new <= 0 or not (ratio[0] <= new / span <= ratio[1]):
                continue
        kept.append((round(t, 4), round(g, 4)))
    return kept


def _lum_warm(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Brightness and warmth (red minus blue): Newtime's grid and waveform are blue-grey, its marker lines orange."""
    a = rgb.astype(float)
    return a.mean(axis=2), a[:, :, 0] - a[:, :, 2]


def bar_lines(rgb: np.ndarray, rows: tuple[int, int], cols: tuple[int, int], dark: float = 45.0) -> list[float]:
    """x of each bar line in the band rows x cols: runs of blue-grey columns whose median brightness is below `dark` (beat lines and the
    plain grid are lighter; orange marker lines are warm and ignored)."""
    lum, warm = _lum_warm(rgb[rows[0]:rows[1], cols[0]:cols[1]])
    cool = np.where(warm < 20, lum, 255.0)
    med = np.median(cool, axis=0)
    hit = np.where(med < dark)[0]
    runs: list[list[int]] = []
    for x in hit:
        if runs and x - runs[-1][-1] <= 1:
            runs[-1].append(int(x))
        else:
            runs.append([int(x)])
    width = cols[1] - cols[0]
    return [cols[0] + float(np.mean(r)) for r in runs if r[0] > 2 and r[-1] < width - 3]   # the editor's own dark edges are not bars


def waveform_profile(rgb: np.ndarray, rows: tuple[int, int], cols: tuple[int, int], light: float = 150.0) -> np.ndarray:
    """Height of the drawn waveform in each column (light, low-colour pixels); columns hidden by a marker line read as NaN."""
    lum, warm = _lum_warm(rgb[rows[0]:rows[1], cols[0]:cols[1]])
    wave = ((lum > light) & (warm < 20)).sum(axis=0).astype(float)
    wave[(warm > 60).sum(axis=0) > 0.5 * (rows[1] - rows[0])] = np.nan
    return wave


def peak_array(y: np.ndarray, sr: int, res_ms: int = 5) -> np.ndarray:
    """Largest absolute sample in each res_ms slice of a mono signal: what a waveform display draws."""
    n = max(1, int(round(sr * res_ms / 1000)))
    y = np.abs(np.asarray(y, dtype=float))
    m = len(y) // n
    return y[:m * n].reshape(m, n).max(axis=1) if m else np.zeros(0)


def peaks_per_column(peaks: np.ndarray, start_s: float, px_per_s: float, width: int, res_ms: int = 5) -> np.ndarray:
    """Largest peak in each column's time span, from a peak_array of res_ms slices (0 before the sample starts or after it ends)."""
    edges = np.floor((1000.0 / res_ms) * (start_s + np.arange(width + 1) / px_per_s)).astype(int)
    out = np.zeros(width)
    for i in range(width):
        lo, hi = edges[i], max(edges[i + 1], edges[i] + 1)
        lo, hi = max(lo, 0), min(hi, len(peaks))
        if hi > lo:
            out[i] = peaks[lo:hi].max()
    return out


def view_map(rgb: np.ndarray, rows: tuple[int, int], cols: tuple[int, int], bar_s: float, approx_start_s: float,
             wave_rows: tuple[int, int] | None = None, peaks: np.ndarray | None = None, res_ms: int = 5, search_bars: int | None = 2,
             min_start_s: float | None = None) -> dict:
    """{start_s (time at cols[0]), px_per_s, bars, first_bar, match}: pixels per second from the bar-line spacing, the time within a bar
    from where the lines fall, and the bar itself from approx_start_s or, when the waveform rows and the audio's peak_array are given, from
    the bar whose audio matches the drawn waveform best (within search_bars of approx_start_s, or anywhere when None, never before
    min_start_s; near-equal matches, such as a repeated chorus, go to the one nearest approx_start_s). match is that correlation."""
    xs = bar_lines(rgb, rows, cols)
    if len(xs) < 2:
        raise ValueError("fewer than two bar lines in view; zoom so at least two bars show")
    gaps = np.diff(xs)
    if np.max(np.abs(gaps / np.median(gaps) - 1.0)) > 0.03:
        raise ValueError("bar lines are unevenly spaced (%s); the view is not a plain grid" % ", ".join("%.0f" % g for g in gaps))
    pps = float(np.median(gaps)) / bar_s
    x0 = xs[0]
    n0 = round((approx_start_s + (x0 - cols[0]) / pps) / bar_s)
    n, match = n0, None
    if wave_rows is not None and peaks is not None and len(peaks):
        prof = waveform_profile(rgb, wave_rows, cols)
        ok = ~np.isnan(prof)
        last = int(len(peaks) * res_ms / 1000.0 / bar_s) + 2
        span = range(n0 - search_bars, n0 + search_bars + 1) if search_bars is not None else range(0, last + 1)
        scores = {}
        for k in span:
            start = k * bar_s - (x0 - cols[0]) / pps
            if min_start_s is not None and start < min_start_s:
                continue
            ref = peaks_per_column(np.asarray(peaks, dtype=float), start, pps, len(prof), res_ms)
            if ok.sum() > 20 and np.std(ref[ok]) > 0 and np.std(prof[ok]) > 0:
                scores[k] = float(np.corrcoef(prof[ok], ref[ok])[0, 1])
        if scores:
            top = max(scores.values())
            n = min((k for k, v in scores.items() if v >= top - 0.02), key=lambda k: abs(k - n0))
            match = round(scores[n], 3)
    return {"start_s": n * bar_s - (x0 - cols[0]) / pps, "px_per_s": pps, "bars": [round(x, 1) for x in xs], "first_bar": int(n) + 1,
            "match": match}


def x_for(t: float, view: dict, left: int) -> float:
    return left + (t - view["start_s"]) * view["px_per_s"]


def handle_span(rgb: np.ndarray, row: int, cols: tuple[int, int], lo: float = 80.0, hi: float = 112.0) -> tuple[int, int]:
    """Left and right x of the scroll handle on its bar row: the mid grey (87, edges 106) on the dark track (57), searched only between
    the arrow buttons (cols), which are drawn in the same grey."""
    lum, _ = _lum_warm(rgb[row:row + 1, cols[0]:cols[1]])
    hit = np.where((lum[0] >= lo) & (lum[0] <= hi))[0]
    if not len(hit):
        raise ValueError("no scroll handle on row %d" % row)
    return cols[0] + int(hit.min()), cols[0] + int(hit.max())


def marker_columns(rgb: np.ndarray, rows: tuple[int, int], cols: tuple[int, int]) -> list[float]:
    """x of each drawn warp marker: columns that are marker orange (255, 184, 113) for most of the editor's height. The playhead line is a
    duller orange (156, 133, 91) and is not counted."""
    lum, warm = _lum_warm(rgb[rows[0]:rows[1], cols[0]:cols[1]])
    tall = ((warm > 100) & (lum > 160)).sum(axis=0) > 0.8 * (rows[1] - rows[0])
    xs, run = [], []
    for x in np.where(tall)[0]:
        if run and x - run[-1] > 1:
            xs.append(cols[0] + float(np.mean(run)))
            run = []
        run.append(int(x))
    if run:
        xs.append(cols[0] + float(np.mean(run)))
    return xs
