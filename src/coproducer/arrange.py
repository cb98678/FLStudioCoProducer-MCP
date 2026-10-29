"""Place vocal chops and FX over a section map by rule, so a new song gets an arrangement from its chop roles instead of a hand-written table.

Roles come from the chop plan (which chop is the hook, which answer it, which word stutters in a build). The rules are the ones the first remix was
built with, written once and run over any list of sections named intro, groove, break, build, drop, outro. Rows are (bar, step, chop name, velocity, key).
"""
from __future__ import annotations

ROLE_KEYS = ("teasers", "hook", "hook_echo", "groove_answers", "groove_tail", "stutter_a", "stutter_b", "stab", "stab_echo", "drop_answers", "closers", "outro_closer")
TEASER_STEPS, TEASER_VELS = (8, 12, 0), (70, 80, 85)


def missing_roles(roles: dict) -> list[str]:
    return [k for k in ROLE_KEYS if k not in roles]


def _sections(sections: list[dict], name: str) -> list[dict]:
    return [s for s in sections if s["name"] == name]


def arrange_chops(sections: list[dict], roles: dict) -> list[tuple]:
    """(bar, step, chop name, velocity 1..127, key) rows for the whole song. Teasers close the intro; the hook opens every fourth groove bar with an answer two bars
    later; builds stutter a word that climbs a semitone a bar and end in 16th stabs; drops alternate hook and answer and close on clear air; the outro repeats the closer."""
    bad = missing_roles(roles)
    if bad:
        raise ValueError("chop roles missing: " + ", ".join(bad))
    e: list[tuple] = []
    for s in _sections(sections, "intro")[:1]:
        e += [(s["end"] - 3 + i, TEASER_STEPS[i], n, TEASER_VELS[i], 60) for i, n in enumerate(roles["teasers"][:3])]
    for s in _sections(sections, "groove")[:1]:
        for b in range(s["start"], s["end"] - 3, 4):
            e.append((b, 0, roles["hook"], 108, 60))
        e += [(s["start"] + 2 + 4 * i, 8, n, 96, 60) for i, n in enumerate(roles["groove_answers"]) if s["start"] + 2 + 4 * i < s["end"]]
        e.append((s["end"] - 1, 8, roles["groove_tail"], 100, 67))
    for s in _sections(sections, "build"):
        first = s["start"]
        for i in range(min(6, s["end"] - first - 2)):
            e.append((first + i, 0, roles["stutter_a"], 82 + 4 * i, 60 + i))
            e.append((first + i, 8, roles["stutter_b"], 78 + 4 * i, 60 + i))
        e += [(s["end"] - 2, st, roles["stab"], 88 + 2 * st, 66) for st in range(0, 12, 4)]
        e.append((s["end"] - 2, 12, roles["stab_echo"], 112, 66))
        e += [(s["end"] - 1, st, roles["stab"], 100 + 2 * st // 2, 72) for st in (0, 2, 4, 6, 8, 10, 12)]
    for n_drop, s in enumerate(_sections(sections, "drop")):
        first, n = s["start"], s["end"] - s["start"]
        last = first + n - 4
        for b in range(first, first + n, 4):
            e.append((b, 2, roles["hook_echo"] if (b - first) % 8 == 4 and b != last else roles["hook"], 112, 60))
            if b != last:
                e.append((b + 2, 10, roles["drop_answers"][0] if (b - first) % 8 == 0 else roles["drop_answers"][1], 100, 60))
        e.append((first + n - 2, 0, roles["closers"][min(n_drop, len(roles["closers"]) - 1)], 100, 60))
    for s in _sections(sections, "outro")[:1]:
        e.append((s["start"] + 2, 0, roles["outro_closer"], 80, 60))
    return sorted(e)


MOMENTS = ("into_drop", "into_build", "break_start", "groove_start", "outro_start", "intro_end")


def generate_fx_cues(sections: list[dict], policy: dict | None = None) -> list[dict]:
    """Impacts, sweeps, risers and downlifters placed on the section boundaries: an impact and an air sweep into every drop, a long riser through every build,
    a short riser before the end of each break and of the intro, an impact and a downlifter where a break or the outro starts.

    A policy (a variety fx option's cues) replaces that for the moments it names: {moment: [cue, ...]} with moments into_drop, into_build
    (a build's first bar), break_start, groove_start, outro_start and intro_end (the intro's last bar), each cue's "bar" an offset from the
    moment's bar and "bars" (risers) capped at the section's length; moments it leaves out keep the default cues."""
    if policy:
        return _policy_cues(sections, policy)
    c: list[dict] = []
    for s in sections:
        n, b = s["name"], s["start"]
        if n == "drop":
            c += [{"kind": "impact", "bar": b, "gain_db": 0.0}, {"kind": "air_sweep", "bar": b - 1, "beats": 8, "gain_db": -3.0}]
        elif n in ("groove", "break", "outro"):
            c.append({"kind": "impact", "bar": b, "gain_db": -9.0, "seconds": 2.2})
            if n in ("break", "outro"):
                c.append({"kind": "downlifter", "bar": b, "beats": 8, "gain_db": -12.0})
            if n == "break" and s["end"] - b >= 8:
                c.append({"kind": "noise_riser", "bar": s["end"] - 4, "bars": 4, "f0": 300, "f1": 9000, "gain_db": -15.0})
        elif n == "build":
            c += [{"kind": "noise_riser", "bar": b, "bars": min(8, s["end"] - b), "f0": 400, "f1": 15000, "gain_db": -10.0},
                  {"kind": "tone_riser", "bar": b, "bars": min(8, s["end"] - b), "f0": 220.0, "f1": 1760.0, "gain_db": -20.0}]
        elif n == "intro" and s["end"] - b >= 8:
            c.append({"kind": "noise_riser", "bar": s["end"] - 4, "bars": 4, "f0": 500, "f1": 7000, "gain_db": -18.0})
    return c


def _policy_cues(sections: list[dict], policy: dict) -> list[dict]:
    default = generate_fx_cues(sections)
    named = {m for m in MOMENTS if m in policy}

    def moment_of(cue: dict) -> str | None:
        """Which moment a default cue belongs to, so a policy that names the moment replaces it."""
        for s in sections:
            if cue["bar"] in (s["start"], s["start"] - 1) and s["name"] == "drop" and cue["kind"] in ("impact", "air_sweep"):
                return "into_drop"
            if cue["bar"] == s["start"] and s["name"] == "build":
                return "into_build"
            if cue["bar"] == s["start"] and s["name"] in ("break", "groove", "outro"):
                return {"break": "break_start", "groove": "groove_start", "outro": "outro_start"}[s["name"]]
            if s["name"] in ("break", "intro") and cue["kind"] == "noise_riser" and cue["bar"] == s["end"] - 4:
                return "intro_end" if s["name"] == "intro" else "break_start"
        return None
    out = [c for c in default if moment_of(c) not in named]
    for s in sections:
        n, b = s["name"], s["start"]
        moments = {"drop": "into_drop", "build": "into_build", "break": "break_start", "groove": "groove_start", "outro": "outro_start"}
        m = moments.get(n)
        targets = [(m, b)] if m else []
        if n == "intro":
            targets.append(("intro_end", s["end"] - 1))
        for mom, at in targets:
            if mom not in named:
                continue
            for cue in policy.get(mom) or []:
                c = dict(cue)
                c["bar"] = max(0, at + int(cue.get("bar", 0)))
                if "bars" in c:
                    c["bars"] = max(1, min(int(c["bars"]), s["end"] - s["start"]))
                out.append(c)
    return sorted(out, key=lambda c: (c["bar"], c["kind"]))
