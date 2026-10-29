"""Section gains: lower or raise a part section by section with one automation clip on a Fruity Balance in its insert, the way the Future House
reference makes its drop land (its vocal chop sits lower in the buildup and comes up on the drop, its sub is silent until the drop, and its master
Balance dips before the drop).

Why: on the tech-house remix (v15, 2026-10-25) the drops measured no louder than the builds and 1.6 LU under the breaks after the master, although
the drops were the loudest sections before it: the master limiter takes several dB more off a dense drop than off a sparse break. Level has to be
shaped before the master. Each insert gets a neutral Fruity Balance (library entry "fh master Fruity Balance") in its last free slot and one clip
spanning the song: 0 dB where no gain is set, the section's gain inside it, with short ramps at the boundaries so nothing clicks.

DEFAULT_ROLE_GAINS is the map the person approved on that song by ear (2026-10-25): with it the drops sat 3.4 to 3.8 LU over the builds (the
reference: 4.5) and 1.9 to 2.6 LU over the breaks, the drops stayed as loud as before and the song's average fell from -11.7 to -13.0 LUFS, because
the drops already sat at the master's ceiling (raising everything 1.5 dB moved them 0.1 LU). It is a starting point for another song, to be
checked with measure_section_levels on the mastered render. Sections match a map kind by the start of their name (Build 1 and Buildup are builds).
"""
from __future__ import annotations

import re

from . import fxlib, partmix
from .automation import PLUGIN_PARAM_BASE, TICKS_PER_BEAT, add_automation_clip, db_to_fader, mixer_link, next_channel_id
from .flpfile import TICKS_PER_BAR, Flp, FlpError
from .pump import BALANCE_ENTRY, BALANCE_VOLUME, free_slot

RAMP_BEATS = 0.25
DEFAULT_ROLE_GAINS = {
    "build": {"kick": -3.0, "clap": -2.0, "hats": -4.0, "reese": -3.0, "sub": -6.0, "arp": -2.0, "chops": -2.0, "master": -6.0},
    "break": {"reese": -3.9, "sub": -7.8, "arp": -3.9, "fx": -2.6},
}


def section_kind(name: str, kinds) -> str | None:
    """The map key a section takes: its own name when the map has it ("Build 1", for a lift one build needs and the others do not), else the
    first kind its name starts with, ignoring case and a trailing number."""
    own = re.sub(r"\s+", " ", name).strip().lower()
    exact = next((k for k in kinds if re.sub(r"\s+", " ", k).strip().lower() == own), None)
    if exact is not None:
        return exact
    base = re.sub(r"[\s\d]+$", "", name).lower()
    return next((k for k in kinds if base.startswith(k)), None)


def gains_by_role(f: Flp, sections: list[dict], role_map: dict) -> list[dict]:
    """Entries for apply_gains from a {kind: {role or "master": dB}} map, one per mixer insert whose part has a role in it (partmix roles)."""
    by_insert: dict[int, tuple[str, dict]] = {}
    roles = {t: partmix.track_role(f, ids) for t, ids in partmix.tracks_in_use(f).items() if t}
    roles[0] = "master"
    for s in sections:
        kind = section_kind(s["name"], role_map)
        for t, role in roles.items():
            key = "reese" if role == "bass" and kind and "bass" not in role_map[kind] else role   # the map's reese is the remix's bass part
            if kind and key in role_map[kind]:
                by_insert.setdefault(t, (role, {}))[1][s["name"]] = float(role_map[kind][key])
    label = {"fx": "FX", "clap": "Snare Clap", "master": "Master"}
    return [{"insert": t, "sections": sec, "label": label.get(role, role.title())} for t, (role, sec) in sorted(by_insert.items())]


def sections_from_markers(f: Flp, song_end_bar: float | None = None) -> list[dict]:
    """[{"name", "start_bar", "end_bar"}] (bars count from 1) from the current arrangement's time markers; the last one runs to the song end."""
    marks = sorted(f.time_markers(), key=lambda m: m["pos"])
    if not marks:
        raise FlpError("the project has no time markers; add them (add_section_markers) or pass sections")
    end = song_end_bar or _song_end_bar(f)
    out = []
    for i, m in enumerate(marks):
        stop = marks[i + 1]["pos"] / TICKS_PER_BAR + 1 if i + 1 < len(marks) else end
        out.append({"name": m["name"], "start_bar": m["pos"] / TICKS_PER_BAR + 1, "end_bar": stop})
    return out


def _song_end_bar(f: Flp) -> float:
    ends = [(int.from_bytes(it[0:4], "little") + int.from_bytes(it[8:12], "little")) / TICKS_PER_BAR for it in f.playlist_items()]
    return max(ends, default=0.0) + 1


def gain_points(sections: list[dict], gains_db: dict, end_beat: float, ramp: float = RAMP_BEATS) -> list[tuple]:
    """Absolute (beat, knob) points: each named section at its gain, every other stretch at 0 dB, ramps of `ramp` beats into each change."""
    def level(beat: float) -> float:
        for s in sections:
            if (s["start_bar"] - 1) * 4 <= beat < (s["end_bar"] - 1) * 4:
                return float(gains_db.get(s["name"], 0.0))
        return 0.0

    marks = sorted({0.0} | {(s["start_bar"] - 1) * 4 for s in sections} | {(s["end_bar"] - 1) * 4 for s in sections})
    pts = [(0.0, db_to_fader(level(0.0)))]
    for b in marks[1:]:
        if b >= end_beat:
            break
        was, now = level(b - 1e-6), level(b)
        if was != now:
            pts += [(max(pts[-1][0], b - ramp), db_to_fader(was)), (b, db_to_fader(now))]
    pts.append((end_beat, db_to_fader(level(end_beat - 1e-6))))
    return [p for i, p in enumerate(pts) if i == 0 or p[0] > pts[i - 1][0] or p[1] != pts[i - 1][1]]


def _slot(f: Flp, insert: int) -> int:
    """The last free slot of a part's insert (after its own effects, like the reference's pump), but the first free slot of the master, so the gain
    acts before the master's limiter."""
    if insert != 0:
        return free_slot(f, insert)
    free = [s for s in range(10) if fxlib.slot_plugin(f, 0, s) is None]
    if not free:
        raise FlpError("the master has no free effect slot")
    return free[0]


def apply_gains(f: Flp, insert: int, gains_db: dict, sections: list[dict], row: int, label: str = "") -> dict:
    """One Balance and one clip for `insert`. Returns where they went."""
    unknown = sorted(set(gains_db) - {s["name"] for s in sections})
    if unknown:
        raise FlpError("no section named %s (sections: %s)" % (", ".join(unknown), ", ".join(s["name"] for s in sections)))
    end = (max(s["end_bar"] for s in sections) - 1) * 4
    slot = _slot(f, insert)
    fxlib.inject(f, insert, slot, fxlib.load_entry(BALANCE_ENTRY))
    fxlib.set_slot_name(f, insert, slot, "Section Gain")
    ch = next_channel_id(f)
    pts = gain_points(sections, gains_db, end)
    add_automation_clip(f, ch, "Section Gain %s" % (label or "Insert %d" % insert), mixer_link(insert, PLUGIN_PARAM_BASE + BALANCE_VOLUME, sub=slot), pts,
                        start_beat=0.0, track=row)
    return {"insert": insert, "slot": slot, "clip": ch, "points": len(pts), "gains_db": dict(gains_db), "length_beats": round(end, 2),
            "length_ticks": int(end * TICKS_PER_BEAT)}


def contrast(rows: list[dict]) -> list[dict]:
    """For each drop section of a measure_section_levels result: LU over the section before it and over the loudest break."""
    kinds = ("intro", "groove", "break", "build", "drop", "outro")
    breaks = [r["lufs"] for r in rows if section_kind(r["section"], kinds) == "break"]
    out = []
    for i, r in enumerate(rows):
        if section_kind(r["section"], kinds) != "drop":
            continue
        prev = rows[i - 1] if i else None
        out.append({"drop": r["section"], "before": prev["section"] if prev else None,
                    "over_before_lu": round(r["lufs"] - prev["lufs"], 2) if prev else None,
                    "over_loudest_break_lu": round(r["lufs"] - max(breaks), 2) if breaks else None})
    return out


def scaled(role_map: dict, scale: float) -> dict:
    """The role map with every gain multiplied by `scale` (the knob the contrast loop turns)."""
    return {kind: {role: round(db * scale, 2) for role, db in roles.items()} for kind, roles in role_map.items()}
