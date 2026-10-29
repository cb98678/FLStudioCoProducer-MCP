from __future__ import annotations

import numpy as np

from coproducer import dsp, newtimeview
from coproducer.result import Result, fail, ok


def detect_warp_markers(path: str, bpm: float, division: int = 4, lead_s: float = -1.0, max_move_s: float = 0.045, delta: float = 0.1) -> Result:
    """Where to put Newtime warp markers on a vocal so Quantize time fits it to the beat: one per syllable onset that is near a grid line.

    Each marker sits at onset + lead_s (the singer's own lead on the grid, measured when lead_s is negative), so quantizing keeps the feel and
    removes the scatter. Returns markers and grid (seconds into the file, grid = where Quantize time will move each one), lead_s, onsets,
    mean_move_ms, duration_s and peaks_5ms (the waveform peaks add_warp_markers_gui matches against Newtime's drawing).
    Errors: E_IO (unreadable file), E_ARG (tempo or division out of range).
    """
    if not (40.0 <= bpm <= 250.0) or division not in (1, 2, 3, 4, 6, 8):
        return fail("E_ARG", "bpm must be 40..250 and division one of 1, 2, 3, 4, 6, 8 (Newtime's snap steps)")
    try:
        x, rate = dsp.load_audio(path)
    except ValueError as e:
        return fail("E_IO", str(e))
    mono = x.mean(axis=1) if x.ndim == 2 else x
    onsets = newtimeview.onset_times(mono, rate, delta=delta)
    lead = newtimeview.best_lead(onsets, bpm, division) if lead_s < 0 else float(lead_s)
    pairs = newtimeview.warp_markers(onsets, bpm, lead, max_move_s, division)
    moves = [abs(t - g) for t, g in pairs]
    return ok({"markers": [t for t, _ in pairs], "grid": [g for _, g in pairs], "lead_s": lead, "onsets": int(len(onsets)),
               "mean_move_ms": round(1000 * float(np.mean(moves)), 1) if moves else 0.0, "duration_s": round(len(mono) / rate, 4),
               "peaks_5ms": [round(float(v), 4) for v in newtimeview.peak_array(mono, rate, 5)]})
