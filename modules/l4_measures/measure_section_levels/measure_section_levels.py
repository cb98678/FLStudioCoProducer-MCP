from __future__ import annotations

import numpy as np

from coproducer import dsp, flpfile, sectiongain
from coproducer.result import Result, fail, ok


def _sections(f, sections: list | None, end_s: float, bpm: float = 0.0) -> tuple[list, float]:
    """[(name, start_s, end_s)] from explicit sections in bars, or from the project's time markers and tempo; [] when neither is usable."""
    bpm = f.tempo() if f else float(bpm or 0.0)
    if sections and bpm:
        bar = 240.0 / bpm
        return [(s["name"], (s["start_bar"] - 1) * bar, (s["end_bar"] - 1) * bar) for s in sections], bpm
    marks = f.time_markers() if f and not sections else []
    if not marks:
        return [], bpm
    tick_s = 60.0 / bpm / flpfile.TICKS_PER_BEAT
    starts = [(m["name"] or "marker %d" % i, m["pos"] * tick_s) for i, m in enumerate(marks)]
    return [(n, a, starts[i + 1][1] if i + 1 < len(starts) else end_s) for i, (n, a) in enumerate(starts)], bpm


def measure_section_levels(path: str, project: str = "", sections: list | None = None, bpm: float = 0.0) -> Result:
    """Loudness, peak, RMS, clipped samples and band balance of each section of a render. Sections come from the project's own time markers (the
    current arrangement) or from a list of {name, start_bar, end_bar} (bar 1 is the start) with the project, or bpm, giving the tempo. Use it to compare
    section contrast with a reference: `contrast` gives each drop's LU over the section before it and over the loudest break (the Future House
    reference: 4.5 over its build). Errors: E_IO, E_ARG."""
    try:
        x, rate = dsp.load_audio(path)
        f = flpfile.Flp.load(project) if project else None
    except (OSError, ValueError, flpfile.FlpError, RuntimeError) as e:
        return fail("E_IO", "cannot read: %s" % e)
    secs, bpm = _sections(f, sections, len(x) / rate, bpm)
    if not secs:
        return fail("E_ARG", "need a project with time markers, or sections in bars together with a project or bpm for the tempo")
    rows = []
    for name, a, b in secs:
        seg = x[int(a * rate) : int(min(b, len(x) / rate) * rate)]
        if len(seg) < rate // 2:
            continue
        rows.append({"section": name, "start_s": round(a, 2), "end_s": round(b, 2), "lufs": round(dsp.integrated_loudness(seg, rate), 2),
                     "peak_db": round(dsp.db(float(np.abs(seg).max())), 2), "rms_db": round(dsp.db(float(np.sqrt(np.mean(seg ** 2)))), 2),
                     "clipped": int((np.abs(seg) >= 0.9999).sum()), "bands_db": dsp.band_energy_db(seg, rate, dsp.DEFAULT_BANDS)})
    if not rows:
        return fail("E_ARG", "no section is half a second long inside the render")
    return ok({"bpm": bpm, "sections": rows, "contrast": sectiongain.contrast(rows)})
