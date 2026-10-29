"""Effect chains as recipes: plugins/chains.json names, for each part role, the effect-library entries that make its chain in the reference's slot
order, and apply_chain puts them into the free slots of that part's insert in one go, after whatever the insert already holds.

The chains come from the Future House reference (docs/REFERENCE_FUTURE_HOUSE.md, "Effect chains"); automation targets, meters and Edison are
left out. A chain was tuned for the reference's own sounds, so it is a starting point: measure the part after it goes in and rebalance its level.
Entries for plugins this FL edition does not own (config fl.not_owned) are skipped and listed.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import fxlib
from .flpfile import Flp, FlpError

CHAINS = Path(__file__).resolve().parents[2] / "plugins" / "chains.json"


def load(path: Path | str = CHAINS) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def chain(name: str, data: dict | None = None) -> dict:
    """The chain for a role or bus name, following "same_as"."""
    chains = (data or load())["chains"]
    seen = set()
    while name in chains and "same_as" in chains[name] and name not in seen:
        seen.add(name)
        name = chains[name]["same_as"]
    if name not in chains:
        raise FlpError("no chain for %r (known: %s)" % (name, ", ".join(sorted(chains))))
    return dict(chains[name], name=name)


def apply_chain(f: Flp, insert: int, name: str, not_owned: tuple = (), data: dict | None = None) -> dict:
    """Inject the chain's entries into the free slots of `insert`, in order, after its last used slot. Refuses when the free slots after it are too few."""
    c = chain(name, data)
    entries = [fxlib.load_entry(e) for e in c["entries"]]
    skipped = [e["name"] for e in entries if e["plugin"] in not_owned]
    entries = [e for e in entries if e["plugin"] not in not_owned]
    used = [s for s in range(10) if fxlib.slot_plugin(f, insert, s)]
    free = [s for s in range(max(used, default=-1) + 1, 10)]
    if len(free) < len(entries):
        raise FlpError("insert %d has %d free slots after its effects; chain %s needs %d" % (insert, len(free), c["name"], len(entries)))
    placed = []
    for slot, e in zip(free, entries):
        fxlib.inject(f, insert, slot, e)
        placed.append({"slot": slot, "entry": e["name"], "plugin": e["plugin"]})
    return {"insert": insert, "chain": c["name"], "placed": placed, "skipped": skipped}
