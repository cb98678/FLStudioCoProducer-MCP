"""A production pass: the Future House reference's production moves applied from a recipe file (recipes/production/*.json) to any arrangement
that has time markers and parts named by role, in one go, so a new song gets them without hand steps.

Order matters for the effect slots: buses and their routing first, then the part chains (they take the first free slots after what an insert
holds), then the pump, transitions and section gains (each in its own named instance in the last free slots), then the house standard. A step
that cannot apply (no free insert for a bus, no snare for a pitch rise, no room in an insert) is listed with the reason and the rest go on.
Every move is one of the tested recipes (mixroute, fxchains, pump, transitions, fxsynth, sectiongain, projorg); this module only decides where.
"""
from __future__ import annotations

import json
import struct
from pathlib import Path

from . import flporg, fxchains, fxsynth, mixroute, partmix, projorg, pump, sectiongain, transitions
from .flpfile import Flp, FlpError

RECIPES = Path(__file__).resolve().parents[2] / "recipes" / "production"


def load_recipe(name: str) -> dict:
    """A production recipe by name (recipes/production/NAME.json) or by path to a JSON file (a song's own recipe: the style's recipe with the
    plan's production_overrides merged, variety.merge_recipe)."""
    if name.lower().endswith(".json") and Path(name).is_file():
        return json.loads(Path(name).read_text(encoding="utf-8"))
    p = RECIPES / ("%s.json" % name)
    if not p.is_file():
        raise FlpError("no production recipe %r (known: %s)" % (name, ", ".join(sorted(x.stem for x in RECIPES.glob("*.json")))))
    return json.loads(p.read_text(encoding="utf-8"))


TARGETS = ("music_bus", "drum_bus", "snare") + tuple(dict.fromkeys(mixroute.MUSIC_ROLES + mixroute.LEAD_ROLES + mixroute.DRUM_ROLES + ("sub", "fx")))


def check_recipe(recipe: dict) -> list[str]:
    """Problems with a production recipe, one sentence each: unknown moves, synths, targets, pump depths or section kinds."""
    kinds = ("intro", "groove", "break", "build", "drop", "outro", "verse", "chorus")
    out = []
    for p in recipe.get("pump", []):
        if p.get("on") not in TARGETS or p.get("depth", "deep") not in pump.DEPTHS or p.get("curve", "linear") not in pump.CURVES:
            out.append("pump %s" % p)
    for pair, moves in recipe.get("transitions", {}).items():
        a, _, b = pair.partition(">")
        if a not in kinds or b not in kinds:
            out.append("transition %r is not kind>kind" % pair)
        for m in moves:
            if "synth" in m:
                if m["synth"] not in fxsynth.PATCHES:
                    out.append("%s: unknown synth %s" % (pair, m["synth"]))
            elif m.get("recipe") not in transitions.RECIPES or m.get("on") not in TARGETS:
                out.append("%s: bad move %s" % (pair, m))
    return out


def _named_insert(f: Flp, name: str) -> int | None:
    return next((t for t in range(1, mixroute.insert_count(f)) if (flporg.insert_name(f, t) or "").lower() == name.lower()), None)


def resolve(f: Flp, target: str) -> tuple[str, int] | None:
    """("insert" or "channel", number) for a recipe target: music_bus, drum_bus, a role (sub, kick, fx...), or snare (the clap or snare channel)."""
    if target in ("music_bus", "drum_bus"):
        t = _named_insert(f, "Music Bus" if target == "music_bus" else "Drum Bus") or (_named_insert(f, "Drums Bus") if target == "drum_bus" else None)
        return ("insert", t) if t else None
    if target == "snare":
        chans = [c for c in f.channel_ids() if partmix.role_of(f.channel_info(c)["name"] or "") == "clap" and f.channel_info(c)["sample"]]
        snare = [c for c in chans if "snare" in (f.channel_info(c)["name"] or "").lower()]
        return ("channel", (snare or chans)[0]) if chans else None
    ins = mixroute.inserts_for_roles(f, (target,))
    return ("insert", ins[0]) if ins else None


def section_pairs(sections: list[dict]) -> list[tuple[str, str, str]]:
    """(from kind, to kind, moment) for each section change; kinds as in sectiongain.section_kind, the moment is the second section's name."""
    kinds = ("intro", "groove", "break", "build", "drop", "outro", "verse", "chorus")
    out = []
    for a, b in zip(sections, sections[1:]):
        ka, kb = sectiongain.section_kind(a["name"], kinds), sectiongain.section_kind(b["name"], kinds)
        if ka and kb:
            out.append((ka, kb, b["name"]))
    return out


def _snapshot(f: Flp) -> tuple:
    return f.head, [[e, v] for e, v in f.events], f.tail


def _restore(f: Flp, snap: tuple) -> None:
    f.head, f.events, f.tail = snap[0], [[e, v] for e, v in snap[1]], snap[2]


def _step(log: list, what: str, f: Flp, fn, *args):
    """Run one move. When it fails, the project is put back as it was before the move (a chain that placed two of its four effects and then
    found no room leaves nothing behind), and the reason is logged. An unexpected error is logged with its type rather than stopping the pass."""
    snap = _snapshot(f)
    try:
        res = fn(f, *args)
        log.append({"step": what, "ok": True, "result": res})
        return res
    except (FlpError, IndexError, KeyError, struct.error) as e:
        _restore(f, snap)
        why = str(e) if isinstance(e, FlpError) else "%s: %s (a bug: report it)" % (type(e).__name__, e)
        log.append({"step": what, "ok": False, "why": why, "rolled_back": True})
        return None


def _transitions(f: Flp, recipe: dict, sections: list[dict], key: str, log: list) -> None:
    row = pump.first_free_row(f)
    for ka, kb, moment in section_pairs(sections):
        for move in recipe.get("transitions", {}).get("%s>%s" % (ka, kb), []):
            what = "%s at %s" % (move.get("recipe") or move.get("synth"), moment)
            if "synth" in move:
                _step(log, what, f, fxsynth.add_fx_synth, move["synth"], moment, row, -1, float(move.get("bars", 0)), key, move.get("volume"))
                continue
            where = resolve(f, move["on"])
            if where is None:
                log.append({"step": what, "ok": False, "why": "no %s in this project" % move["on"]})
                continue
            kind, num = where
            _step(log, what, f, transitions.add_transition, move["recipe"], moment, row, num if kind == "insert" else -1, num if kind == "channel" else -1,
                  float(move.get("bars", 4)), float(move.get("beats", 2)), int(move.get("semitones", 12)), float(move.get("period", 1.0)), float(move.get("low", 0.4)))


def apply(f: Flp, recipe: dict, key: str = "A", not_owned: tuple = ()) -> list[dict]:
    """Run the recipe on a loaded project; returns the log of steps (each ok or with the reason it did not apply)."""
    sections = sectiongain.sections_from_markers(f)
    log: list[dict] = []
    for bus in recipe.get("buses", []):
        have = _named_insert(f, bus["name"]) or (_named_insert(f, "Drums Bus") if bus["kind"] == "drums" else None)
        if have:  # a family bus from the house standard (build_family_buses) already does the job
            log.append({"step": "bus %s" % bus["name"], "ok": True, "result": {"bus": have, "already": True}})
            continue
        sources = mixroute.inserts_for_roles(f, mixroute.MUSIC_ROLES if bus["kind"] == "music" else mixroute.DRUM_ROLES)
        _step(log, "bus %s" % bus["name"], f, mixroute.build_bus, bus["name"], sources)
    if recipe.get("chains"):
        known = fxchains.load()
        for name in known["chains"]:
            for t in mixroute.inserts_for_roles(f, (name,)):
                _step(log, "chain %s on insert %d" % (name, t), f, fxchains.apply_chain, t, name, not_owned, known)
        mb = _named_insert(f, "Music Bus")
        if mb:
            _step(log, "chain music_bus on insert %d" % mb, f, fxchains.apply_chain, mb, "music_bus", not_owned, known)
    if recipe.get("pump"):
        kick = next((c for c in f.channel_ids() if partmix.role_of(f.channel_info(c)["name"] or "") == "kick" and f.note_ticks(c)), None)
        targets = [{"insert": w[1], "depth": p.get("depth", "deep"), **({"depth_db": float(p["depth_db"])} if "depth_db" in p else {}),
                    **({"curve": p["curve"]} if p.get("curve") else {})}
                   for p in recipe["pump"] if (w := resolve(f, p["on"])) and w[0] == "insert"]
        if kick is None or not targets:
            log.append({"step": "pump", "ok": False, "why": "no kick with notes or no pump target"})
        else:
            _step(log, "pump", f, pump.build_pump, kick, targets, pump.first_free_row(f))
    _transitions(f, recipe, sections, key, log)
    gains = recipe.get("section_gains")
    if gains == "after_render":
        log.append({"step": "section gains", "ok": False, "why": "left for after the first render: " + recipe.get("section_gains_how", "")})
    elif gains:
        role_map = sectiongain.DEFAULT_ROLE_GAINS if gains == "default" else gains
        row = pump.first_free_row(f)
        for k, g in enumerate(sectiongain.gains_by_role(f, sections, role_map)):
            _step(log, "section gains on insert %d" % g["insert"], f, sectiongain.apply_gains, g["insert"], g["sections"], sections, row + k, g["label"])
    if recipe.get("standard"):
        _step(log, "house standard", f, lambda g: projorg.apply(g, projorg.plan(g)))
    return log
