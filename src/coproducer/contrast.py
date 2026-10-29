"""The contrast loop's decisions, as pure functions: how far to turn the section-gain scale so every drop sits lo..hi LU over its build, how far
each quiet section kind must come up to sit within the targets' floor under the drops, and the by_role map for apply_section_gains that does
both within what one Fruity Balance can do. tools/remix_song.py renders and measures between turns.

Measured on the first genre renders (2026-10-25): drop over build moves about 7.5 LU per unit of scale (7.3 to 7.8 on dubstep, dnb and
techno), so a first turn aimed with that slope lands near the middle of the window instead of overshooting from 0.4 to 8.1 LU at scale 1. A
section lift past Balance's top (+5.6 dB) is done by lowering every other section by the excess, which keeps every relative level; the master
sets the final loudness anyway.
"""
from __future__ import annotations

import re

SLOPE_LU = 7.5
BALANCE_MAX_DB = 5.5
LIFT_MAX_DB = 12.0
FLOOR_KINDS = ("intro", "groove", "break", "outro")


def kind_of(name: str, kinds) -> str | None:
    """The kind a section name belongs to (Build 1 is a build), ignoring case and a trailing number."""
    base = re.sub(r"[\s\d]+$", "", name).lower()
    return next((k for k in kinds if base.startswith(k)), None)


def drop_over_build(contrast_rows: list[dict]) -> float | None:
    """The smallest drop-over-build LU among drops that follow a build (sectiongain.contrast rows); None when no drop follows a build. A hook
    after a verse (hip-hop has no builds) is not a build contrast: the gain map does not move it (four hip-hop renders stayed at 0.2 LU)."""
    rows = [c["over_before_lu"] for c in contrast_rows if c.get("over_before_lu") is not None and kind_of(c.get("before") or "", ("build",))]
    return min(rows) if rows else None


def stuck(hist: list[tuple[float, float | None]], min_change_lu: float = 0.3) -> bool:
    """True when the last two turns at different scales moved the contrast by less than min_change_lu: the map does not reach it."""
    pts = [(s, w) for s, w in hist if w is not None]
    if len(pts) < 2:
        return False
    (s0, w0), (s1, w1) = pts[-2], pts[-1]
    return s0 != s1 and abs(w1 - w0) < min_change_lu


def blocked(hist: list[tuple[float, float | None]], lo: float, hi: float) -> bool:
    """True when the section-gain map cannot move the contrast the way it must go: drops already more than hi LU over their builds at the
    lowest scale (the map only adds contrast; a quiet build by design, a silent beat before the drop), too little at the highest, or the next
    scale would be the one just rendered. Measured 2026-10-28: two varied remixes sat at 5.8 and 7.4 LU at scale 0 and rendered four more
    times at the clamped 0.05 without moving."""
    s1, w1 = hist[-1]
    if w1 is None or lo <= w1 <= hi:
        return False
    if (w1 > hi and s1 <= 0.05) or (w1 < lo and s1 >= 3.0):
        return True
    return len(hist) > 1 and next_scale(hist, lo, hi) == s1


def build_lift(hist: list[tuple[float, float | None]], lo: float, hi: float, lifted_db: float = 0.0) -> float:
    """dB to raise the builds when the drops sit more than hi LU over them and the map cannot help (blocked): aimed at the middle of lo..hi,
    0 when no lift is needed or the builds already took LIFT_MAX_DB. A quiet build by design (a 4-bar lift, a silent beat) stays the quieter
    section, just not a hole: 2026-10-28, an afro house remix with 4-bar builds sat 11 LU under its drops."""
    w = hist[-1][1]
    if w is None or w <= hi or not blocked(hist, lo, hi):
        return 0.0
    return round(max(0.0, min(LIFT_MAX_DB - lifted_db, w - (lo + hi) / 2)), 2)


def next_scale(hist: list[tuple[float, float | None]], lo: float, hi: float, slope_lu: float = SLOPE_LU) -> float:
    """The next scale, aimed at the middle of lo..hi from the last point: by the slope of the last two turns at different scales when there
    are two, else slope_lu. hist is [(scale, worst drop-over-build LU)]; kept within 0.05..3."""
    s1, w1 = hist[-1]
    if w1 is None:
        return s1
    prev = next(((s0, w0) for s0, w0 in reversed(hist[:-1]) if s0 != s1 and w0 is not None), None)
    slope = (w1 - prev[1]) / (s1 - prev[0]) if prev and w1 != prev[1] else slope_lu
    if slope <= 0:
        slope = slope_lu
    return round(min(3.0, max(0.05, s1 + ((lo + hi) / 2 - w1) / slope)), 3)


def shortfall(sections: list[dict], floor_lu: float, tolerance_lu: float = 0.5) -> dict:
    """dB each section kind (intro, groove, break, outro) must come up so that its quietest section sits within floor_lu of the loudest drop.
    sections: measure_section_levels rows {"section", "lufs"}. Kinds already within tolerance_lu are left out."""
    drops = [r["lufs"] for r in sections if kind_of(r["section"], ("drop",)) and r.get("lufs") is not None]
    if not floor_lu or not drops:
        return {}
    need: dict = {}
    for r in sections:
        kind = kind_of(r["section"], FLOOR_KINDS)
        if kind and r.get("lufs") is not None:
            gap = (max(drops) - floor_lu) - r["lufs"]
            if gap > tolerance_lu:
                need[kind] = round(max(need.get(kind, 0.0), gap), 2)
    return need


def add_lifts(lifts: dict, need: dict) -> dict:
    """Lifts so far plus what the last render still needs, each capped at LIFT_MAX_DB."""
    out = dict(lifts)
    for kind, gap in need.items():
        out[kind] = round(min(LIFT_MAX_DB, out.get(kind, 0.0) + gap), 2)
    return out


def role_map(base: dict, scale: float, lifts: dict, kinds) -> dict:
    """The by_role map for apply_section_gains: base scaled (the contrast knob), plus each kind's lift on the master insert. When a lift passes
    BALANCE_MAX_DB, every kind in `kinds` (the song's section kinds) is lowered by the excess instead, so all relative levels hold."""
    out = {kind: {role: round(db * scale, 2) for role, db in roles.items()} for kind, roles in base.items()} if scale else {}
    shift = max(0.0, max(lifts.values(), default=0.0) - BALANCE_MAX_DB)
    for kind in sorted(set(kinds) | set(lifts)):
        g = lifts.get(kind, 0.0) - shift
        if g:
            out.setdefault(kind, {})["master"] = round(out.get(kind, {}).get("master", 0.0) + g, 2)
    return out


def section_lifts(contrast_rows: list[dict], lo: float, hi: float, lifted: dict | None = None) -> dict:
    """dB per build, by its section name, for each drop that sits more than hi LU over its own build: aimed at the middle of lo..hi, each
    build's total capped at LIFT_MAX_DB. Returns the totals (lifted plus this turn's). The kind-wide map moves every build together, so a
    remix whose builds differ (an 8-bar riserchorus beside a 4-bar lift) kept two drops at 6.0 LU while the third sat at 3.8, and the loop,
    which reads only the smallest contrast, stopped there (Open Your Heart, 2026-10-29)."""
    out = dict(lifted or {})
    mid = (lo + hi) / 2
    for c in contrast_rows:
        b, v = c.get("before") or "", c.get("over_before_lu")
        if v is None or v <= hi or not kind_of(b, ("build",)):
            continue
        add = round(min(LIFT_MAX_DB - out.get(b, 0.0), v - mid), 2)
        if add >= 0.25:
            out[b] = round(out.get(b, 0.0) + add, 2)
    return out


def with_section_lifts(role_map: dict, lifts_by_name: dict, kinds) -> dict:
    """role_map plus one entry per lifted section: its kind's roles with the master raised by the lift (sectiongain takes a section's own
    name over its kind). A master past BALANCE_MAX_DB lowers every kind and section by the excess instead, as role_map does."""
    out = {k: dict(v) for k, v in role_map.items()}
    for name, db in lifts_by_name.items():
        if not db:
            continue
        kind = kind_of(name, sorted(set(kinds) | set(role_map), key=len, reverse=True))
        entry = dict(role_map.get(kind, {})) if kind else {}
        entry["master"] = round(entry.get("master", 0.0) + db, 2)
        out[name] = entry
    excess = max([e.get("master", 0.0) for e in out.values()] + [0.0]) - BALANCE_MAX_DB
    if excess > 0:
        for k in set(kinds) | set(out):
            e = out.setdefault(k, {})
            e["master"] = round(e.get("master", 0.0) - excess, 2)
    return out


def shortfall_each(sections: list[dict], floor_lu: float, tolerance_lu: float = 0.5) -> dict:
    """dB each intro, groove, break or outro section must come up, by its own name, to sit within floor_lu of the loudest drop. The kind-wide
    shortfall lifts every section of a kind by its quietest one's gap: on Open Your Heart (2026-10-29) a 4-bar break after drop 1 that was
    never short rose 5.5 dB with the quiet riserchorus break and ended 0.7 LU under the drops."""
    drops = [r["lufs"] for r in sections if kind_of(r["section"], ("drop",)) and r.get("lufs") is not None]
    if not floor_lu or not drops:
        return {}
    need: dict = {}
    for r in sections:
        if kind_of(r["section"], FLOOR_KINDS) and r.get("lufs") is not None:
            gap = (max(drops) - floor_lu) - r["lufs"]
            if gap > tolerance_lu:
                need[r["section"]] = round(gap, 2)
    return need
