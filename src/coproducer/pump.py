"""Pumping without a compressor sidechain: an automation clip on a Fruity Balance volume knob in each pumped insert, dipping on every kick note.

The Future House reference pumps with a Fruity Envelope Controller linked to Love Philter. Copying that controller into another project (identical
channel block and identical link bytes, only the channel id changed) did not pump in FL's command-line render, while the original did (2026-10-25,
sandbox/pumpcheck*), so the cause is not in the bytes we can see. Automation clips that we write do render (docs/FLP_FORMAT.md, "Automation clips"),
and the reference itself rides Fruity Balance volume knobs with clips, so this is the pump we build: a neutral Fruity Balance from the effect
library in a free slot, and one clip per pumped insert that follows the kick. Proof is a render: measure_pump_depth, pumped against not pumped.
"""
from __future__ import annotations

import math
import struct

from . import fxlib
from .automation import TICKS_PER_BEAT, add_automation_clip, db_to_fader, mixer_link, next_channel_id, PLUGIN_PARAM_BASE
from .flpfile import Flp, FlpError

BALANCE_ENTRY = "fh master Fruity Balance"
BALANCE_VOLUME = 1  # Fruity Balance parameter 1; 0.8 is 0 dB, the same law as a mixer fader
DEPTHS = {"full": -24.0, "deep": -16.0, "medium": -8.0}  # a requested -12 dB measured -7 dB on the first 16th of the beat, so ask deeper
HOLD_BEATS, RELEASE_BEATS = 0.1, 0.3  # the reference's pump, measured on renders with and without its links (2026-10-25): 14 to 21 dB down for
# about a tenth of a beat, back to full level by about 0.3 beat


def first_free_row(f: Flp) -> int:
    """The playlist row just below every row that holds an item (rows count from 1 at the top)."""
    rows = [499 - struct.unpack_from("<H", it, 12)[0] for it in f.playlist_items()]
    return max(rows, default=0) + 1


def free_slot(f: Flp, insert: int) -> int:
    slots = [s for s in range(10) if fxlib.slot_plugin(f, insert, s) is None]
    if not slots:
        raise FlpError("insert %d has no free effect slot" % insert)
    return slots[-1]  # last, so the pump acts on the processed sound, as the reference's bus pump does


CURVES = ("linear", "exp")


def _recovery(b: float, hold: float, release: float, depth_db: float) -> list[tuple]:
    """Points of an exponential recovery between the hold and the release: fast at first, then easing into 0 dB (gain 1 - e^(-x/tau),
    tau half the recovery: Red Lights' synth bus as the person's breakdown draws it, about -3 dB 60 ms after a 40 ms hold at 125 bpm)."""
    span, out = release - hold, []
    for frac in (0.15, 0.3, 0.5, 0.75):
        g = 1.0 - math.exp(-frac * 2.0)
        out.append((b + hold + frac * span, db_to_fader(max(depth_db, 20.0 * math.log10(g)))))
    return out


def pump_points(kick_beats: list[float], end_beat: float, depth_db: float, release: float = RELEASE_BEATS, hold: float = HOLD_BEATS,
                curve: str = "linear") -> list[tuple]:
    """Knob points: 0 dB, a dip to depth_db on each kick held for `hold` beats, back to 0 dB `release` beats after the kick: in a straight
    line, or with curve "exp" fast at first and easing in (_recovery)."""
    normal, low = db_to_fader(0.0), db_to_fader(depth_db)
    pts: list[tuple] = [(0.0, normal)]
    for b in kick_beats:
        if b <= 1e-6:
            pts = [(0.0, low)]  # a kick on the first beat: start the clip in the dip
        else:
            while len(pts) > 1 and pts[-1][0] >= b - 1e-6:
                pts.pop()  # the next kick comes before the last one recovered: stay in the dip
            if b - 0.01 > pts[-1][0] + 1e-6 and pts[-1][1] == normal:
                pts.append((b - 0.01, normal))
            pts.append((b, low))
        if 0 < hold < release:
            pts.append((b + hold, low))
            if curve == "exp":
                pts += _recovery(b, hold, release, depth_db)
        pts.append((b + release, normal))
    if end_beat > pts[-1][0]:
        pts.append((end_beat, normal))
    return pts


def build_pump(f: Flp, kick: int, targets: list[dict], row: int) -> dict:
    """targets: [{"insert", "depth": full|deep|medium or "depth_db", "slot" and "curve" (linear or exp) optional}]. One clip per target on
    playlist row `row`."""
    ticks = sorted(set(f.note_ticks(kick)))
    if not ticks:  # a kick under a Layer has its notes on the Layer
        ticks = sorted({t for c in f.channel_ids() if kick in f.layer_children(c) for t in f.note_ticks(c)})
    if not ticks:
        raise FlpError("the kick channel %d plays no notes on the playlist" % kick)
    beats = [t / TICKS_PER_BEAT for t in ticks]
    end = beats[-1] + 1.0
    entry, placed = fxlib.load_entry(BALANCE_ENTRY), []
    for t in targets:
        ins = int(t["insert"])
        slot = int(t["slot"]) if t.get("slot") is not None else free_slot(f, ins)
        fxlib.inject(f, ins, slot, entry)
        fxlib.set_slot_name(f, ins, slot, "Pump")
        depth = float(t.get("depth_db", DEPTHS[t.get("depth", "deep")]))
        ch = next_channel_id(f)
        curve = t.get("curve", "linear")
        add_automation_clip(f, ch, "Pump %d" % ins, mixer_link(ins, PLUGIN_PARAM_BASE + BALANCE_VOLUME, sub=slot), pump_points(beats, end, depth, curve=curve), track=row)
        placed.append({"insert": ins, "slot": slot, "depth_db": depth, "clip": ch, "curve": curve})
    return {"kick_notes": len(ticks), "targets": placed}
