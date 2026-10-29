from __future__ import annotations

import numpy as np

from coproducer import dsp
from coproducer.result import Result, fail, ok

BINS = 16


def measure_pump_depth(path: str, bpm: float, start_s: float = 0.0, end_s: float = 0.0) -> Result:
    """How much a part ducks on each beat: the level folded over one beat (16 bins, bin 0 is the beat; the window starts on the first beat line at or after start_s, counted from the start of the render) as the median beat of the window (beats without a kick do not wash out the dip), the depth in dB
    (loudest bin minus quietest) and where the dip sits. A pumped part shows its dip at or just after bin 0 and a depth of several dB; an unpumped
    part shows a flat curve. Use a solo render of the part (split_part_projects keeps the pump's controller on). Errors: E_IO, E_ARG."""
    if bpm <= 0:
        return fail("E_ARG", "bpm must be positive")
    try:
        x, rate = dsp.load_audio(path)
    except (OSError, ValueError, RuntimeError) as e:
        return fail("E_IO", "cannot read %s: %s" % (path, e))
    beat = 60.0 / bpm * rate
    first = int(np.ceil(start_s * rate / beat) * beat)  # fold from a beat line (beats counted from the start of the render)
    m = dsp.mono(x)[first : int(end_s * rate) if end_s else None]
    beats = int(len(m) // beat)
    if beats < 2:
        return fail("E_ARG", "the window holds fewer than two beats")
    rows = []
    for b in range(beats):
        seg = m[int(b * beat) : int((b + 1) * beat)]
        edges = np.linspace(0, len(seg), BINS + 1).astype(int)
        rows.append([dsp.power_db(float(np.mean(seg[edges[k] : edges[k + 1]] ** 2))) for k in range(BINS)])
    arr = np.array(rows)
    level = arr.max(axis=1)
    keep = arr[level >= level.max() - 20.0]  # beats where the part plays; silent beats would pull the median to the floor
    # the median beat in dB: beats without a kick (a break) do not wash out the dip the way an energy mean does
    curve = [round(float(v), 2) for v in np.median(keep, axis=0)]
    if max(curve) <= dsp.FLOOR_DB + 1:
        return fail("E_ARG", "the window is silent")
    low = int(np.argmin(curve))
    return ok({"depth_db": round(max(curve) - min(curve), 2), "dip_bin": low, "curve_db": curve, "beats": beats, "beats_used": int(len(keep))})
