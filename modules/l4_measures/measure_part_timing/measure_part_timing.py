from __future__ import annotations

from coproducer import dsp, flpfile, parttiming
from coproducer.result import Result, fail, ok


def measure_part_timing(path: str, project: str = "", channel: str = "", times_s: list[float] | None = None, tolerance_ms: float = 10.0) -> Result:
    """Check that a solo render of one part lands on its notes. Give the render (`path`) and either the project and channel name (the note times come
    from the playlist and tempo) or the expected times in seconds. Returns the median offset, spread and notes outside the tolerance in ms."""
    try:
        x, rate = dsp.load_audio(path)
        if times_s is None:
            f = flpfile.Flp.load(project)
            ids = [c for c in f.channel_ids() if f.channel_info(c)["name"] == channel]
            if not ids:
                return fail("E_NOT_FOUND", "no channel named %r" % channel)
            times_s = parttiming.note_times_s(f, ids[0])
    except (ValueError, OSError, flpfile.FlpError) as e:
        return fail("E_IO", str(e))
    if not times_s:
        return fail("E_ARG", "no expected note times")
    offsets = parttiming.onset_offsets_ms(x, rate, list(times_s))
    return ok({**parttiming.summarize(offsets, tolerance_ms), "offsets_ms": offsets[:200]})
