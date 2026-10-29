"""Mixer routing written into a project file, and buses built from it, the way the Future House reference routes its parts.

The reference sends its drums (kick, clap, hats) to a Drum Group bus and its melodic parts (vocal chops, keys, mid bass, outro synth) to one music
bus called Sidechain that carries the sweepable filter, the throw reverb and the pump; the sub, the fills and the FX skip both buses and go straight
to the master, so a filter sweep or a pump on the music never touches them. That layout is what the transition and pump recipes act on.

Routing is event 235 of an insert's block: one byte per destination insert, 1 for a route (0 is the master); FL 26 drops the trailing zeros. A bus
here is an existing insert that nothing uses yet (no channel, no effect, no name, routed only to the master); FL 21 and later let a project hold
fewer than 127 inserts, so when none is free the person adds inserts in FL first. The last insert of such a project routes nowhere (FL's own) and
is never used. Send levels other than unity live in the mixer records and are left as they are.
"""
from __future__ import annotations

from . import flporg, partmix
from .fxlib import slot_plugin
from .flpfile import Flp, FlpError

EV_FLAGS, EV_ROUTE = 236, 235
BUS_COLOR = (255, 235, 59)  # the house standard's bus yellow
MUSIC_ROLES = ("chops", "stab", "arp", "reese", "bass", "synth", "orig")  # the reference's music bus: chops, keys, mid bass, lead synth
LEAD_ROLES = ("vocal",)  # the lead vocal skips the music bus like the sub: no pump on the words, and a stop bar leaves the last words hanging.
# Girlish Type Men (2026-10-29): the spoken lead on the deep-pumped music bus measured 20 dB under the music in the first chorus.
DRUM_ROLES = ("kick", "clap", "hats", "perc")


def _marks(f: Flp) -> list[int]:
    return [i for i, (e, _v) in enumerate(f.events) if e == EV_FLAGS]


def _route_index(f: Flp, insert: int) -> int:
    marks = _marks(f)
    if not 0 <= insert < len(marks):
        raise FlpError("insert %d not in the file (it has %d)" % (insert, len(marks)))
    stop = marks[insert + 1] if insert + 1 < len(marks) else len(f.events)
    for k in range(marks[insert] + 1, stop):
        if f.events[k][0] == EV_ROUTE:
            return k
    raise FlpError("insert %d has no routing event" % insert)


def insert_count(f: Flp) -> int:
    return len(_marks(f))


def routes(f: Flp, insert: int) -> list[int]:
    """Destination inserts of `insert` (0 is the master)."""
    return [k for k, b in enumerate(bytes(f.events[_route_index(f, insert)][1])) if b == 1]


def set_routes(f: Flp, insert: int, dests: list[int]) -> None:
    """Route `insert` to exactly these destinations. An insert cannot route to itself; the master routes nowhere."""
    n = insert_count(f)
    if insert == 0 or insert in dests or any(not 0 <= d < n for d in dests):
        raise FlpError("cannot route insert %d to %s" % (insert, dests))
    data = bytearray(max(dests) + 1 if dests else 1)
    for d in dests:
        data[d] = 1
    f.events[_route_index(f, insert)][1] = bytes(data)


def _used_tracks(f: Flp) -> set[int]:
    return {f.channel_info(c)["track"] for c in f.channel_ids()} - {None}


def blank_inserts(f: Flp) -> list[int]:
    """Inserts with no channel, no effect and no name that nothing routes into (FL's last insert excluded), whatever they route to."""
    n = insert_count(f)
    used = _used_tracks(f)
    targets = {d for i in range(1, n) for d in routes(f, i)}
    return [i for i in range(1, n - 1) if i not in used and i not in targets and not flporg.insert_name(f, i)
            and not any(slot_plugin(f, i, s) for s in range(10))]


def free_inserts(f: Flp) -> list[int]:
    """Blank inserts routed only to the master: what a bus takes first. A project converted from FL 20 can route every insert to extra
    inserts as well (the Future House demo sends its empty ones to 100 to 103); build_bus falls back to those blank inserts and resets their routing."""
    return [i for i in blank_inserts(f) if routes(f, i) == [0]]


def inserts_for_roles(f: Flp, roles: tuple) -> list[int]:
    """Part inserts whose role (from their channels' names, else the insert's name) is in `roles`."""
    out = []
    for t, ids in sorted(partmix.tracks_in_use(f).items()):
        if t == 0:
            continue
        role = partmix.track_role(f, ids) or partmix.role_of(flporg.insert_name(f, t) or "")
        if role in roles:
            out.append(t)
    return out


def _top(f: Flp, insert: int, bus: int) -> int:
    """The insert to reroute for a part: the part itself, or the family bus it already feeds, so family buses keep working."""
    seen = {insert}
    cur = insert
    while True:
        up = [d for d in routes(f, cur) if d not in (0, bus)]
        if len(up) != 1 or up[0] in seen:
            return cur
        cur = up[0]
        seen.add(cur)


def build_bus(f: Flp, name: str, sources: list[int], bus: int | None = None) -> dict:
    """Make a named bus on a free insert (or the one given) and route `sources` (or the family buses they feed) into it, off the master."""
    if not sources:
        raise FlpError("no part inserts to route into %s" % name)
    free = free_inserts(f) or blank_inserts(f)
    if bus is None:
        if not free:
            raise FlpError("no free mixer insert for %s: add an insert in FL (or pass bus) first" % name)
        bus = free[0]
    elif bus not in free:
        raise FlpError("insert %d is in use; free inserts: %s" % (bus, free))
    set_routes(f, bus, [0])
    moved = sorted({_top(f, s, bus) for s in sources})
    for s in moved:
        set_routes(f, s, [bus])
    flporg.set_insert(f, bus, name=name, rgb=BUS_COLOR)
    return {"bus": bus, "name": name, "routed": moved, "parts": sorted(sources)}
