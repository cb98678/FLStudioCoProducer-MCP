"""Each song's own sounds: library candidates for a part, and the history that keeps a sound from coming back in another song (2026-11-07).

The person: "the sounds match the songs, not a forced preference. we choose or create new sounds for every song ... that goes for the
bass as well ... each song, every element is unique, not copied over from a preference sheet." So no part has a default sound. For each
part of each song, select_part_sound auditions a few presets from the Serum 2 library (the Factory folders for the part's role and the
person's own banks, never the generated sandbox folder) against the original's part, adds one sound made for it (match_part_sound) and
keeps the nearest. The history (sandbox\\sound_history.json) records every choice; a preset another song or another part already took is
never a candidate again. The candidates are drawn from a seed (the song, the part and an optional seed word), spread over the role's
folders, so each song hears a different set and a re-run of the same song hears the same set.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

EXT = ".serumpreset"
MADE_PREFIX = "CP - "   # the name every sound made here gets ("CP - <Song> <Part>"): made for one song, never a candidate for another
# The Serum 2 Factory folders a role's candidates come from (path pieces under Presets, matched anywhere in the path, case-insensitive).
ROLE_FOLDERS = {
    "sub": ("bass/sub", "bass/808"),
    "bass": ("bass/reese", "bass/modulated", "bass/synth", "bass/hard", "bass/acid", "bass/retro analog", "bass/electric", "bass/misc", "bass/808"),
    "stab": ("chord", "pluck", "keyboard", "e piano", "synth", "brass", "organ"),
    "chords": ("chord", "pluck", "keyboard", "e piano", "synth", "brass", "organ"),
    "arp": ("arp", "seq", "pluck", "bell", "mallet"),
    "pluck": ("pluck", "arp", "bell", "mallet", "guitar"),
    "pad": ("pad", "string", "soundscape", "chord"),
    "lead": ("lead", "synth", "vox", "brass", "woodwind"),
    "keys": ("keyboard", "e piano", "piano", "organ"),
}
# Words in a preset's name that put a preset from the person's own banks (no role folders there) into a role's candidates.
ROLE_WORDS = {
    "sub": ("sub", "808"), "bass": ("bass", "reese", "growl", "808"), "stab": ("chord", "stab", "pluck", "key", "keys", "pl"),
    "chords": ("chord", "stab", "pluck", "key", "keys", "pl"), "arp": ("arp", "seq", "pluck", "pl"), "pluck": ("pluck", "pl", "bell"),
    "pad": ("pad", "string", "strings", "atmos", "texture"), "lead": ("lead", "ld", "synth"), "keys": ("key", "keys", "piano", "organ", "ep"),
}
# The three presets the builder used to fall back to for every song (until 2026-11-07): they count as taken by those earlier remixes.
EARLIER = ("CP - Deep Sub", "PL Crusty Pluck [LCV]", "ARP - Jno Style")


def _tokens(text: str) -> set[str]:
    out, word = set(), ""
    for c in text.lower():
        if c.isalnum():
            word += c
        else:
            out.add(word)
            word = ""
    return (out | {word}) - {""}


def catalog(library_dir: str, role: str) -> list[dict]:
    """[{name, path, rel, folder}] of the .SerumPreset files under library_dir that suit the role: a Factory file in one of the role's folders,
    or a file in the person's own banks (a path with a part named User) whose name has one of the role's words. Never a sound made
    here for an earlier song (a folder named sandbox, or a name starting "CP - ")."""
    root = Path(library_dir)
    if not root.is_dir():
        return []
    out = []
    for p in sorted(root.rglob("*")):
        if p.suffix.lower() != EXT or not p.is_file():
            continue
        parts = [x.lower() for x in p.relative_to(root).parent.parts]
        if "sandbox" in parts or p.stem.startswith(MADE_PREFIX):
            continue   # sounds made for earlier songs (sandbox/<song>, or the older "CP - " ones in the person's banks) are theirs
        joined = "/" + "/".join(parts) + "/"
        folder = next((f for f in ROLE_FOLDERS.get(role, ()) if "/" + f + "/" in joined), None)
        if folder is None and "user" in parts and _tokens(p.stem) & set(ROLE_WORDS.get(role, ())):
            folder = "user"
        if folder:
            out.append({"name": p.stem, "path": str(p), "rel": p.relative_to(root).as_posix(), "folder": folder})
    return out


def load_history(path: str) -> dict:
    """{song: {role: {preset, path, source, distance}}} from the history file, {} when there is none or it cannot be read."""
    p = Path(path)
    try:
        d = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
    except (OSError, ValueError):
        return {}
    return d.get("songs", {}) if isinstance(d, dict) else {}


def taken(history: dict, song: str, role: str) -> set[str]:
    """Preset names (lower case) no candidate may have: every earlier song's choices, this song's other parts, and EARLIER."""
    out = {n.lower() for n in EARLIER}
    for s, parts in history.items():
        for r, row in (parts or {}).items():
            if not (s == song and r == role) and row.get("preset"):
                out.add(str(row["preset"]).lower())
    return out


def _rank(song: str, role: str, seed: str, rel: str) -> str:
    return hashlib.sha256(("%s|%s|%s|%s" % (song, role, seed, rel)).encode("utf-8")).hexdigest()


def candidates(cat: list[dict], song: str, role: str, used: set[str], k: int, seed: str = "") -> list[dict]:
    """Up to k presets of the catalog no one has used, drawn per song (a seeded order) and spread over the role's folders in turn."""
    by: dict[str, list[dict]] = {}
    for row in sorted(cat, key=lambda r: _rank(song, role, seed, r["rel"])):
        if row["name"].lower() not in used:
            by.setdefault(row["folder"], []).append(row)
    order = sorted(by, key=lambda f: _rank(song, role, seed, f))
    out: list[dict] = []
    while len(out) < k and any(by.values()):
        for f in order:
            if by[f] and len(out) < k:
                out.append(by[f].pop(0))
    return out


def record(path: str, song: str, role: str, row: dict) -> None:
    """Write the part's choice into the history file (a re-run of the same song and part replaces its row)."""
    p = Path(path)
    hist = load_history(path)
    hist.setdefault(song, {})[role] = {k: row.get(k) for k in ("preset", "path", "source", "distance")}
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"songs": hist}, indent=1) + "\n", encoding="utf-8")


def audition(sound: dict, role: str, key_pc: int) -> list[dict]:
    """The notes every candidate plays: the part's own measured notes, or the key's root, fifth and octave four times (an octave up from
    C2 for a low part)."""
    if sound.get("audition_notes"):
        return sound["audition_notes"]
    root = (36 if role in ("sub", "bass") else 60) + key_pc
    return [{"pitch": p, "start": 2.0 * k, "duration": 1.0, "velocity": 100} for k in range(4) for p in ((root,) if root < 48 else (root, root + 7, root + 12))]


def slug(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name).strip("_")
