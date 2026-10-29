"""Variety: each remix chooses its own form, groove, kit, bass line, chord treatment, arp, sounds, transitions, mix and vocal treatment
from the option bank (src/coproducer/data/options), learned from the twenty FL Studio demo songs (docs/DEMO_STUDY.md), so no two
remixes share a format.

The person (2026-10-28): "you keep making the same format and same song over and over again and this is not the point of this. I need
variation and creativity." Every earlier remix used the same section template, drums, bass pocket, stab, rising arp, risers and pump.

How a choice is made, per category: options are scored against the song's brief (the style's genres, the song's moods and energy, its
tempo), options used by recent remixes lose points (the history file, most recent first: the last remix -3, the two before -1.5, up to
ten back -0.5), and one is drawn at random among the best few, weighted by score, from a seed (the song's name by default, so a plan is
reproducible; another seed gives another valid plan). One category can take a "surprise": an option from another genre, the creative
risk the brief asks for. Locked choices (the person's or the agent's decision) are kept as given.

The result is plain data in the plan: plan["variety"] (the choices, the alternatives, why) and plan["style_overrides"] (the realized pack
fields, editable), plan["production_overrides"] (moves merged into the production recipe), plan["kit"] and plan["instruments"].
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import random
from pathlib import Path

OPTIONS = Path(__file__).resolve().parent / "data" / "options"
CATEGORIES = ("form", "drums", "kit", "bass", "chords", "arp", "harmony", "fx", "mix", "vocal", "automation")
SOUND_ROLES = ("stab", "arp", "bass", "sub")
SURPRISE_CATS = ("arp", "fx", "chords", "bass")  # not drums or form: those change the genre itself, not its colour
PENALTY = ((1, 3.0), (3, 1.5), (10, 0.5))  # (how many remixes back, points lost)
TOP = 4          # draw among this many best options
TEMPERATURE = 0.7

# A style pack's name to the genre words the bank uses (the pack name is always one of them).
STYLE_GENRES = {
    "house": ["house", "deep_house", "garage", "nu_disco", "tech_house", "future_house", "afro_house", "pop_dance"], "club_house": ["house", "tech_house", "future_house"],
    "deep_house": ["deep_house", "house", "afro_house", "organic_house"], "tech_house": ["tech_house", "house", "minimal"],
    "tech_house_groove": ["tech_house", "house", "minimal"],
    "techno": ["techno", "melodic_techno", "industrial_techno", "minimal"], "dnb": ["drum_and_bass", "dnb", "liquid_dnb", "jungle"],
    "dubstep": ["dubstep", "melodic_dubstep", "halftime", "bass_house"], "trap": ["trap", "drill", "hiphop"], "hiphop": ["hiphop", "boom_bap", "lofi", "trap"],
    "nu_disco": ["nu_disco", "pop_dance", "funk", "house"],
    "afro_house": ["afro_house", "deep_house", "organic_house", "amapiano"], "afrobeats": ["afrobeats", "afro_pop", "amapiano", "dancehall"],
    "reggaeton": ["reggaeton", "latin", "dancehall", "moombahton"], "trance": ["trance", "progressive_house", "uplifting_trance"],
    "melodic_techno": ["melodic_techno", "techno", "progressive_house"], "liquid_dnb": ["liquid_dnb", "drum_and_bass", "dnb"],
    "future_bass": ["future_bass", "melodic_dubstep", "pop"], "uk_drill": ["uk_drill", "drill", "trap", "grime"],
    "lofi": ["lofi", "chillhop", "jazz_hop", "hiphop"], "trip_hop": ["trip_hop", "downtempo", "lounge"], "pop_dance": ["pop_dance", "nu_disco", "pop", "house"],
    "future_house": ["future_house", "bass_house", "house"], "big_room": ["big_room", "edm", "electro_house"],
    "electro_industrial": ["electro_industrial", "ebm", "industrial_techno"], "cinematic": ["soundtrack", "cinematic", "spy", "jazz"],
}
ENERGY = {"low": 0, "mid": 1, "high": 2}
# How much a genre match counts, per category: a form, a vocal treatment or a mix move is about the song (its structure, its singer, its
# mood) more than its genre, so mood and energy weigh more there; drums, bass, kits and sounds are where the genre lives.
GENRE_WEIGHT = {"form": 1.5, "vocal": 1.5, "mix": 2.0, "automation": 2.0, "fx": 2.0}


class VarietyError(ValueError):
    """A lock names an unknown option, or the bank is malformed."""


def load_bank(folder: Path | str = OPTIONS) -> dict[str, list[dict]]:
    """{category: [options]} from every options file (sources.json is the provenance table, not options)."""
    out: dict[str, list[dict]] = {}
    for p in sorted(Path(folder).glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        if "options" in d:
            out[d["category"]] = d["options"]
    return out


def sources(folder: Path | str = OPTIONS, which: tuple = ("songs", "remixes", "references")) -> dict:
    """The sources options cite: the FL demo songs ("songs"), the professional remixes studied against their originals ("remixes") and
    the published records the person brought breakdowns of ("references", skill song-blueprints)."""
    d = json.loads((Path(folder) / "sources.json").read_text(encoding="utf-8"))
    out: dict = {}
    for k in which:
        out.update(d.get(k) or {})
    return out


def find(bank: dict, oid: str) -> dict:
    for opts in bank.values():
        for o in opts:
            if o["id"] == oid:
                return o
    raise VarietyError("no option %r in the bank" % oid)


def genres_for(style: str, extra: list[str] | None = None) -> set[str]:
    return set([style] + STYLE_GENRES.get(style, []) + list(extra or []))


def _seed(seed) -> int:
    return int(hashlib.sha256(str(seed).encode()).hexdigest()[:12], 16)


def recent_ids(history: list[dict] | None) -> list[set[str]]:
    """Option ids per earlier remix, most recent first."""
    out = []
    for h in history or []:
        ids = set((h.get("choices") or {}).values()) | set((h.get("sounds") or {}).values())
        out.append({i for i in ids if i})
    return out


def score(opt: dict, genres: set[str], moods: set[str], energy: str | None, bpm: float | None, recent: list[set[str]], weight: float = 3.0) -> float:
    g = set(opt.get("genres", []))
    s = weight if g & genres else 1.0 if "*" in g else 0.0
    om = set(opt.get("moods", []))
    s += 1.0 * len(om & moods) if moods else 0.0
    if "*" in om:
        s += 0.5
    if energy and opt.get("energy") in ENERGY and energy in ENERGY:
        s -= 0.5 * abs(ENERGY[opt["energy"]] - ENERGY[energy])
    lo_hi = opt.get("tempo")
    if bpm and lo_hi and not lo_hi[0] - 2 <= bpm <= lo_hi[1] + 2:
        s -= 2.0
    for k, ids in enumerate(recent):
        if opt["id"] in ids:
            s -= next(p for n, p in PENALTY if k < n) if k < PENALTY[-1][0] else 0.0
    return round(s, 3)


def _draw(rng: random.Random, rows: list[tuple[float, dict]]) -> dict:
    best = sorted(rows, key=lambda r: (-r[0], r[1]["id"]))[:TOP]
    top = best[0][0]
    w = [math.exp((sc - top) / TEMPERATURE) for sc, _ in best]
    x = rng.random() * sum(w)
    for wi, (_sc, o) in zip(w, best):
        x -= wi
        if x <= 0:
            return o
    return best[-1][1]


def choose(brief: dict, *, seed=None, history: list[dict] | None = None, lock: dict | None = None, surprise: bool = True,
           bank: dict | None = None) -> dict:
    """The song's choices. brief: {"style", "genres" (extra genre words), "moods", "energy" (low, mid, high), "bpm", "has_roots" (the record
    gives the chords: harmony keeps them), "sounds" (how many parts take a demo instrument, default 2)}. lock: {category or "sound.ROLE": option
    id}. Returns {"seed", "choices": {category: id}, "sounds": {role: id}, "alternatives": {category: [ids]}, "why": {category: text},
    "surprise": {"category", "id", "from"} or None}."""
    bank = bank or load_bank()
    lock = dict(lock or {})
    rng = random.Random(_seed(seed if seed is not None else brief.get("name", "song")))
    genres = genres_for(brief.get("style", ""), brief.get("genres"))
    moods = {m.lower() for m in brief.get("moods") or []}
    recent = recent_ids(history)
    out: dict = {"seed": seed, "choices": {}, "sounds": {}, "alternatives": {}, "why": {}, "surprise": None}
    for key, oid in lock.items():
        find(bank, oid)  # an unknown lock is an error, not a silent default
    cats = [c for c in CATEGORIES if c in bank and c != "sound"]
    sur = None
    if surprise:
        pool = [c for c in SURPRISE_CATS if c in cats and c not in lock]
        sur = pool[rng.randrange(len(pool))] if pool else None
    for cat in cats:
        rows = [(score(o, genres, moods, brief.get("energy"), brief.get("bpm"), recent, GENRE_WEIGHT.get(cat, 3.0)), o) for o in bank[cat]
                if not o.get("ask_first")]   # an ask-first option (vocal chops as an instrument) is only ever locked in
        if cat == "harmony" and brief.get("has_roots", True) and cat not in lock:
            keep = find(bank, "harmony.keep_original")
            out["choices"][cat], out["why"][cat] = keep["id"], "the record gives its chords bar by bar: the remix keeps them (voicing and rhythm change)"
            out["alternatives"][cat] = [o["id"] for _s, o in sorted(rows, key=lambda r: -r[0])[:3] if o["id"] != keep["id"]]
            continue
        if cat in lock:
            o = find(bank, lock[cat])
            out["choices"][cat], out["why"][cat] = o["id"], "locked"
            continue
        if cat == sur:
            far = [(1.0 + rng.random() - 0.4 * sum(o["id"] in ids for ids in recent[:3]), o) for sc, o in rows if not set(o.get("genres", [])) & genres]
            felt = [r for r in far if set(r[1].get("moods", [])) & moods]
            far = felt or far   # borrow across genres, not across feelings
            if far:
                o = _draw(rng, far)
                out["choices"][cat] = o["id"]
                out["why"][cat] = "surprise: borrowed from %s (%s)" % (", ".join(o.get("genres", [])[:2]), o["label"])
                out["surprise"] = {"category": cat, "id": o["id"], "from": o.get("genres", [])[:3]}
                out["alternatives"][cat] = [x["id"] for _s, x in sorted(rows, key=lambda r: -r[0])[:3]]
                continue
        fit = [r for r in rows if set(r[1].get("genres", [])) & (genres | {"*"})]
        good = [r for r in (fit or rows) if r[0] > 0] or fit or rows   # the genre's own options; moods and history rank them
        o = _draw(rng, good)
        sc = next(s for s, x in rows if x is o)
        out["choices"][cat] = o["id"]
        out["why"][cat] = "%s (score %.1f: %s)" % (o["label"], sc, _reason(o, genres, moods, recent))
        out["alternatives"][cat] = [x["id"] for _s, x in sorted(good, key=lambda r: -r[0]) if x["id"] != o["id"]][:3]
    if "sound" in bank:
        want = int(brief.get("sounds", 2))
        roles = list(SOUND_ROLES)
        rng.shuffle(roles)
        out["sounds"].update({r: lock["sound.%s" % r] for r in roles if "sound.%s" % r in lock})   # locked sounds count toward want
        for role in roles:
            if role in out["sounds"] or len(out["sounds"]) >= want:
                continue
            rows = [(score(o, genres, moods, brief.get("energy"), brief.get("bpm"), recent), o) for o in bank["sound"] if o["engine"]["role"] == role]
            good = [r for r in rows if r[0] >= 3.0]
            if good:
                out["sounds"][role] = _draw(rng, good)["id"]
    return out


def _reason(o: dict, genres: set, moods: set, recent: list) -> str:
    bits = []
    g = sorted(set(o.get("genres", [])) & genres)
    if g:
        bits.append("genre " + ", ".join(g[:2]))
    m = sorted(set(o.get("moods", [])) & moods)
    if m:
        bits.append("mood " + ", ".join(m[:2]))
    if any(o["id"] in ids for ids in recent[:3]):
        bits.append("used recently")
    return "; ".join(bits) or "fits"


# ---- realizing the choices

def overrides(choices: dict, bank: dict | None = None) -> dict:
    """The pack fields the choices set: {"drums": {kind: spec, "swing": x}, "bass": {...}, "sub": {...}, "chords": {...}, "pad": {...}, "arp": {...},
    "form": {...}, "template": [[kind, bars]...]}. Only what the options give; the pack keeps the rest."""
    bank = bank or load_bank()
    ov: dict = {}
    c = choices.get("choices", choices)
    if c.get("form"):
        o = find(bank, c["form"])
        ov["form"] = dict(o.get("engine", {}))
        if o.get("template"):
            ov["template"] = [list(x) for x in o["template"]]
    if c.get("drums"):
        e = find(bank, c["drums"]).get("engine", {})
        if e.get("sections"):
            ov["drums"] = {k: copy.deepcopy(v) for k, v in e["sections"].items()}
            if "swing" in e:
                ov["drums"]["swing"] = e["swing"]
    if c.get("bass"):
        e = find(bank, c["bass"]).get("engine", {})
        if e.get("bass"):
            ov["bass"] = copy.deepcopy(e["bass"])
        if e.get("sub"):
            ov["sub"] = copy.deepcopy(e["sub"])
        if "sub_duck_kicks" in e:
            ov["sub_duck_kicks"] = bool(e["sub_duck_kicks"])
        if e.get("pedal"):
            ov.setdefault("bass", {})["pedal"] = list(e["pedal"])
            ov.setdefault("sub", {})["pedal"] = list(e["pedal"])
    if c.get("chords"):
        e = find(bank, c["chords"]).get("engine", {})
        ch = copy.deepcopy(e.get("pattern", {}))
        for k in ("voicing", "top_only"):
            if k in e:
                ch[k] = e[k]
        if ch:
            ov["chords"] = ch
        if e.get("pad"):   # a chords option with a held pad layer under its hits (its own part in the build)
            ov["pad"] = copy.deepcopy(e["pad"])
    if c.get("arp") and find(bank, c["arp"]).get("engine"):
        ov["arp"] = copy.deepcopy(find(bank, c["arp"])["engine"])
    return ov


def apply_overrides(pack: dict, ov: dict) -> dict:
    """A copy of the pack with the overrides in: drum kinds and role kinds replaced one by one (the pack keeps kinds the option does not
    name), chords and arp replaced whole, form and its section lengths set (intro, build and outro bars; the template for chop plans)."""
    p = copy.deepcopy(pack)
    for role in ("drums", "bass", "sub"):
        if role in ov:
            p.setdefault(role, {}).update(copy.deepcopy(ov[role]))
    if "chords" in ov:
        p.setdefault("chords", {}).update(copy.deepcopy(ov["chords"]))
    if "arp" in ov:
        p["arp"] = copy.deepcopy(ov["arp"])
    if "pad" in ov:
        p["pad"] = copy.deepcopy(ov["pad"])
    if "sub_duck_kicks" in ov:
        p["sub_duck_kicks"] = ov["sub_duck_kicks"]
    if "form" in ov:
        f = ov["form"]
        p["form"] = copy.deepcopy(f)
        lengths = {"intro": f.get("intro_bars"), "build": f.get("build_bars"), "outro": f.get("outro_bars")}
        secs = [[k, int(lengths[k]) if lengths.get(k) else n] for k, n in p["sections"]]
        p["sections"] = [list(x) for x in ov.get("template", secs)]
    return p


def fx_policy(choices: dict, bank: dict | None = None) -> dict | None:
    c = choices.get("choices", choices)
    if not c.get("fx"):
        return None
    cues = find(bank or load_bank(), c["fx"]).get("engine", {}).get("cues")
    return None if cues in (None, "default") else cues


def production_patch(choices: dict, bank: dict | None = None) -> dict:
    """Moves for the production recipe from the fx, mix and automation choices: {"pump": [...] (the mix choice's, when it names one),
    "buses": [...], "transitions": {pair: [moves]}}."""
    bank = bank or load_bank()
    c = choices.get("choices", choices)
    patch: dict = {"transitions": {}}
    for cat in ("fx", "automation", "mix"):
        if not c.get(cat):
            continue
        e = find(bank, c[cat]).get("engine", {})
        prod = dict(e.get("production", {}))
        if cat == "fx" and e.get("transitions"):
            prod.setdefault("transitions", {})
            for pair, moves in e["transitions"].items():
                prod["transitions"].setdefault(pair, []).extend(moves)
        for pair, moves in prod.get("transitions", {}).items():
            patch["transitions"].setdefault(pair, []).extend(copy.deepcopy(moves))
        for k in ("pump", "buses", "pump_source"):
            if k in prod:
                patch[k] = copy.deepcopy(prod[k])
    return patch


def merge_recipe(recipe: dict, patch: dict) -> dict:
    """The production recipe with a song's patch: its pump and buses replace the recipe's when given, its transition moves replace the
    recipe's moves of the same recipe or synth at that section pair and add the rest."""
    r = copy.deepcopy(recipe)
    for k in ("pump", "buses", "pump_source"):
        if k in patch:
            r[k] = copy.deepcopy(patch[k])
    tr = r.setdefault("transitions", {})
    for pair, moves in patch.get("transitions", {}).items():
        names = {m.get("recipe") or m.get("synth") for m in moves}
        tr[pair] = [m for m in tr.get(pair, []) if (m.get("recipe") or m.get("synth")) not in names] + copy.deepcopy(moves)
    return r


def kit(choices: dict, bank: dict | None = None) -> dict:
    """{voice: sample path} from the kit choice (FL factory paths kept as FL writes them)."""
    c = choices.get("choices", choices)
    if not c.get("kit"):
        return {}
    return dict(find(bank or load_bank(), c["kit"]).get("engine", {}).get("voices", {}))


def instruments(choices: dict, bank: dict | None = None) -> dict:
    """{part: {"option", "label", "import": {song, flp, channels, names}, "register", "serum_start"}} for the sound choices: the demo
    instrument a part should use (imported into the remix as the part's channel when the build has the demo's render copy) or, with Serum,
    the direction its generated sound should take."""
    bank = bank or load_bank()
    out = {}
    for role, oid in (choices.get("sounds") or {}).items():
        o = find(bank, oid)
        out[role] = {"option": oid, "label": o["label"], "import": o["engine"]["import"], "register": o.get("register"),
                     "plugin": o.get("plugin"), "preset": o.get("preset"), "serum_start": o.get("serum_start"), "measured": o.get("measured")}
    return out


def _bar_chords(entry) -> tuple[list, int | None]:
    """A loop entry's chords: [offset, quality] is one chord for the bar; [[offset, quality], [offset, quality], step] is two, the second
    from that 16th step on (7 for a change pushed a 16th ahead of beat 3)."""
    if isinstance(entry[0], (list, tuple)):
        return [tuple(entry[0]), tuple(entry[1])], int(entry[2]) if len(entry) > 2 else 8
    return [tuple(entry)], None


def _loop_tonic(engine: dict, key_pc: int, mode: str) -> int:
    """The pitch class the loop's offsets count from: the song's tonic, or (an option with follow_mode) its relative major or minor when
    the loop is written for the other mode (a major loop under a minor song starts from the minor tonic's relative major)."""
    lm = engine.get("mode")
    if engine.get("follow_mode") and lm and mode and lm != mode:
        return (key_pc + (3 if lm == "major" else 9)) % 12
    return key_pc


def harmony_loop(choices: dict, key_pc: int, bank: dict | None = None, mode: str = "") -> tuple[list[int], dict] | None:
    """(roots8, {pitch class: quality}) for a chosen harmony loop, or None to keep the record's chords. roots8 holds each bar's first
    chord; harmony_splits gives the bars that change chord inside the bar."""
    c = choices.get("choices", choices)
    if not c.get("harmony"):
        return None
    eng = find(bank or load_bank(), c["harmony"]).get("engine", {})
    loop = eng.get("loop")
    if not loop:
        return None
    tonic = _loop_tonic(eng, key_pc, mode)
    roots, qual = [], {}
    for entry in loop[:8]:
        chords, _step = _bar_chords(entry)
        roots.append((tonic + int(chords[0][0])) % 12)
        for off, q in chords:
            qual.setdefault((tonic + int(off)) % 12, q)
    return roots, qual


def harmony_splits(choices: dict, key_pc: int, bank: dict | None = None, mode: str = "") -> list | None:
    """Per loop bar, None or [step, pitch class] when the bar's second chord starts at that 16th; None when no bar of the loop splits."""
    c = choices.get("choices", choices)
    if not c.get("harmony"):
        return None
    eng = find(bank or load_bank(), c["harmony"]).get("engine", {})
    tonic = _loop_tonic(eng, key_pc, mode)
    out = []
    for entry in (eng.get("loop") or [])[:8]:
        chords, step = _bar_chords(entry)
        out.append([step, (tonic + int(chords[1][0])) % 12] if step is not None else None)
    return out if any(out) else None


def reharmonizes(choices: dict, bank: dict | None = None) -> bool:
    """Whether the harmony choice replaces the record's chords under the whole song (engine reharmonize), not only where it has none."""
    c = choices.get("choices", choices)
    return bool(c.get("harmony")) and bool(find(bank or load_bank(), c["harmony"]).get("engine", {}).get("reharmonize"))


def describe(choices: dict, bank: dict | None = None) -> list[str]:
    """One line per choice, for the plan's notes and the person."""
    bank = bank or load_bank()
    lines = []
    for cat, oid in choices.get("choices", {}).items():
        o = find(bank, oid)
        lines.append("%s: %s" % (cat, o["label"]) + (" (surprise)" if (choices.get("surprise") or {}).get("id") == oid else ""))
    for role, oid in choices.get("sounds", {}).items():
        lines.append("sound for %s: %s" % (role, find(bank, oid)["label"]))
    return lines


# ---- history

def load_history(path: Path | str) -> list[dict]:
    p = Path(path)
    if not p.is_file():
        return []
    try:
        rows = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return list(reversed(rows)) if isinstance(rows, list) else []


def record(path: Path | str, name: str, result: dict, when: str = "") -> int:
    """Add a remix's choices to the history file (oldest first on disk). Returns how many remixes it holds. A rebuild of the same plan (same
    name, same choices) replaces its row; another version of the same song is a new row, so the next draft avoids every earlier version."""
    p = Path(path)
    rows = list(reversed(load_history(p)))
    rows = [r for r in rows if not (r.get("name") == name and r.get("choices") == result.get("choices", {}))] + [{"name": name, "when": when, "choices": result.get("choices", {}), "sounds": result.get("sounds", {})}]
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
    return len(rows)
