"""Compare two FL projects the way a producer would: what changed in channels, sounds, levels, notes and clips.

Used after a person hand-fixes a build: the report says what they changed, so the recipe that made the build can be changed to match.
Channels are matched by name (ids are renumbered by the builder). Read only.
"""
from __future__ import annotations

from collections import Counter

from . import flpfile
from .automation import fader_to_db

STEP_TICKS = flpfile.TICKS_PER_BEAT // 4  # a 16th note
MIXER_TRACKS = range(0, 126)


def _channels(f: flpfile.Flp) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for ch in f.channel_ids():
        info = f.channel_info(ch)
        info["id"] = ch
        out[info["name"] or "channel %d" % ch] = info
    return out


def mixer_db(f: flpfile.Flp, track: int) -> float | None:
    try:
        raw = f.mixer_volume(track)
    except flpfile.FlpError:
        return None
    return None if raw is None else round(fader_to_db(raw / 16000.0), 1)


def _tempo(f: flpfile.Flp) -> float | None:
    try:
        return f.tempo()
    except flpfile.FlpError:
        return None


def _note_profile(f: flpfile.Flp, ch: int) -> dict:
    ticks = f.note_ticks(ch)
    steps = Counter((t % flpfile.TICKS_PER_BAR) // STEP_TICKS for t in ticks)
    return {"notes": len(ticks), "steps": dict(sorted(steps.items()))}


def _clips(f: flpfile.Flp) -> dict[str, list[tuple]]:
    names = {ch: i["name"] for ch, i in ((c, f.channel_info(c)) for c in f.channel_ids())}
    out: dict[str, list[tuple]] = {}
    for c in f.audio_clips():
        out.setdefault(names.get(c["channel"], str(c["channel"])), []).append((c["pos"], c["length"], round(c["start_ms"]), round(c["end_ms"])))
    return {k: sorted(v) for k, v in out.items()}


def diff_projects(a: flpfile.Flp, b: flpfile.Flp) -> dict:
    """What differs between project a (before) and project b (after). Every list is empty when nothing changed."""
    ca, cb = _channels(a), _channels(b)
    rep: dict = {"tempo": [_tempo(a), _tempo(b)] if _tempo(a) != _tempo(b) else None}
    rep["channels_added"] = sorted(set(cb) - set(ca))
    rep["channels_removed"] = sorted(set(ca) - set(cb))
    changed = []
    for name in sorted(set(ca) & set(cb)):
        for key in ("sample", "preset", "enabled", "track"):
            if ca[name][key] != cb[name][key]:
                changed.append({"channel": name, "field": key, "before": ca[name][key], "after": cb[name][key]})
    rep["channel_changes"] = changed
    mixer = []
    for t in MIXER_TRACKS:
        x, y = mixer_db(a, t), mixer_db(b, t)
        if x is not None and y is not None and abs(x - y) >= 0.2:
            mixer.append({"track": t, "before_db": x, "after_db": y, "delta_db": round(y - x, 1)})
    rep["mixer"] = mixer
    notes = []
    for name in sorted(set(ca) & set(cb)):
        pa, pb = _note_profile(a, ca[name]["id"]), _note_profile(b, cb[name]["id"])
        if pa != pb:
            notes.append({"channel": name, "before": pa, "after": pb})
    rep["notes"] = notes
    qa, qb = _clips(a), _clips(b)
    rep["audio_clips"] = [{"channel": k, "before": qa.get(k, []), "after": qb.get(k, [])} for k in sorted(set(qa) | set(qb)) if qa.get(k) != qb.get(k)]
    return rep


def summarize(rep: dict) -> list[str]:
    """The report as plain sentences, one per finding."""
    out = []
    if rep["tempo"]:
        out.append("tempo %s to %s bpm" % tuple(rep["tempo"]))
    out += ["channel added: " + n for n in rep["channels_added"]] + ["channel removed: " + n for n in rep["channels_removed"]]
    out += ["%s: %s %r to %r" % (c["channel"], c["field"], c["before"], c["after"]) for c in rep["channel_changes"]]
    out += ["mixer track %d: %+.1f dB (%.1f to %.1f)" % (m["track"], m["delta_db"], m["before_db"], m["after_db"]) for m in rep["mixer"]]
    out += ["%s notes: %d to %d, steps %s to %s" % (n["channel"], n["before"]["notes"], n["after"]["notes"], n["before"]["steps"], n["after"]["steps"]) for n in rep["notes"]]
    out += ["%s audio clips changed: %d to %d" % (c["channel"], len(c["before"]), len(c["after"])) for c in rep["audio_clips"]]
    return out
