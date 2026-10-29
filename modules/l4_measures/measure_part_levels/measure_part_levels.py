from __future__ import annotations

from coproducer import partmix
from coproducer.result import Result, fail, ok


def measure_part_levels(solo_dir: str, render_dir: str) -> Result:
    """Loudness (LUFS) and peak of each solo-rendered part and its level relative to the kick, by role. Run it on an approved mix and keep `profile`
    to set the levels of later builds with compare_part_levels. Parts with no render are listed in `missing`."""
    try:
        _man, levels, roles, missing = partmix.measure_dir(solo_dir, render_dir)
        profile = partmix.profile_from(levels, roles)
    except (OSError, ValueError, KeyError) as e:
        return fail("E_IO", str(e))
    parts = [{"track": t, "role": roles[t], **levels[t]} for t in sorted(levels)]
    return ok({"parts": parts, "profile": profile, "missing": missing})
