"""Layer channels and stacked samples, built the way the Future House reference builds its kick (one Layer channel playing three kick samples that
share an insert) and its bass (one Layer channel playing a sub and a mid bass on two inserts).

A Layer channel (type 3) makes no sound: each event 94 in its block names a channel it plays, and every note on the Layer plays all of them. Its
block comes from the effect library (entry "fh layer", the reference's own KICK layer). The part's notes move from its channel to the Layer, so
nothing plays twice. A stacked sample is a copy of an existing sampler (same insert, envelope and settings) that points at another file, with its
own pitch and level. FL keeps a Layer's children where they are in the rack; they can sit in any group. The Layer's own volume knob scales
everything it plays, so it is set to 100% and the levels are set on the children.
"""
from __future__ import annotations

from . import flporg, fxlib
from .flpfile import Flp, FlpError

LAYER_ENTRY = "fh layer"
BANDS = {"top": ("hp", 32, 0), "body": ("lp", 76, 64)}  # channel filters, measured on white noise 2026-10-25 (docs/FLP_FORMAT.md): high-pass at 32
# keeps the click (corner about 4 kHz, -10 dB at 1.3 kHz, -36 dB at 80 Hz); low-pass at 76 keeps the body (corner about 120 Hz, the reference's body kick)
LAYER_VOLUME = 12800  # a Layer's volume knob scales every channel it plays: at 12800 (100%) a layered kick rendered exactly as the kick alone,
# at FL's default 10000 it was 5.2 dB quieter (measured 2026-10-25, sandbox/fcheck/layercal)


def _next_id(f: Flp) -> int:
    return max(f.channel_ids()) + 1


def find_channel(f: Flp, ref) -> int:
    """A channel id from an id or a name (case-insensitive, the first match)."""
    if isinstance(ref, int) or (isinstance(ref, str) and ref.isdigit()):
        ch = int(ref)
        if ch not in f.channel_ids():
            raise FlpError("no channel %d" % ch)
        return ch
    for ch in f.channel_ids():
        if (f.channel_info(ch)["name"] or "").lower() == str(ref).lower():
            return ch
    raise FlpError("no channel named %r" % ref)


def stack_sample(f: Flp, like: int, sample: str, name: str, pitch_cents: int = 0, volume: int | None = None, band: str = "full", pan: float = 0.0) -> int:
    """A new sampler channel copied from `like` (its insert, envelope and settings) playing another file. band "top" high-passes it (keeps the click) and
    "body" low-passes it (keeps the sub), with the channel filter; pan -1..1 spreads a stack (the reference pans two of its three claps). Returns its id."""
    if f.channel_info(like)["sample"] is None:
        raise FlpError("channel %d is not a sampler, so a sample cannot be stacked from it" % like)
    nid = _next_id(f)
    f.clone_channel(like, nid, name)
    f.set_sample(nid, sample, name)
    if pitch_cents:
        f.set_channel_pitch(nid, int(pitch_cents))
    if volume is not None:
        f.set_channel_volume_raw(nid, volume)
    if pan:
        f.set_channel_pan(nid, pan)
    if band != "full":
        if band not in BANDS:
            raise FlpError("band must be full, top or body")
        f.set_channel_filter(nid, *BANDS[band])
    return nid


def add_layer(f: Flp, name: str, children: list, take_notes_from=None, entry: dict | None = None) -> dict:
    """Add a Layer channel playing `children` (ids or names) and give it the notes of `take_notes_from` (default: the first child). Returns the
    layer id, its children and how many notes moved."""
    kids = [find_channel(f, c) for c in children]
    if len(kids) < 2 or len(set(kids)) != len(kids):
        raise FlpError("a layer needs at least two different channels")
    for c in kids:
        if f.layer_children(c):
            raise FlpError("channel %d is a Layer itself; layer its channels instead" % c)
    src = kids[0] if take_notes_from is None else find_channel(f, take_notes_from)
    nid = _next_id(f)
    fxlib.add_channel(f, entry or fxlib.load_entry(LAYER_ENTRY), nid, name, track=0)
    f.set_layer_children(nid, kids)
    f.set_channel_volume_raw(nid, LAYER_VOLUME)
    try:
        flporg.set_channel_group(f, nid, flporg.channel_group(f, kids[0]))
    except FlpError:
        pass  # a file without group events keeps the entry's group
    moved = f.move_notes(src, nid)
    return {"layer": nid, "name": name, "children": kids, "notes_from": src, "moved_notes": moved}
