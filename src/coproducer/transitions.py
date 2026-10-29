"""Transition automation recipes, the ones the Future House reference uses around its section changes.

Each recipe names a target, a moment (a time marker of the current arrangement or a bar number, bar 1 is the start) and a length, and writes
automation clips on plugin parameters, putting the plugin it needs into a free slot first. Every placed plugin is named after its job (slot name
"Transition Filter", "Throw Reverb" and so on), so later recipes reuse that instance and never take over a plugin of the part's own chain, the
pump's Balance or a section gain's Balance (two clips on one knob fight).

- filter_sweep: a high-pass Fruity Filter rises over `bars` bars, thinning the part into the moment, and snaps open on it (the reference's filter
  is set to high-pass: cutoff 0 lets everything through, 0.42 is the top of its sweep). Put it on the music bus.
- reverb_throw: a Fruity Reeverb 2's wet level rises over the last `beats` beats before the moment and drops to nothing on it, while its dry
  level dips to 82% (the reference does both on its music bus).
- pitch_rise: a channel's pitch rises by `semitones` (default 12) over `bars` bars and snaps back at the moment (a rising snare roll). Measured
  in FL's render (2026-10-25): a channel pitch clip maps 0..1 to -48..+48 semitones whatever the pitch knob's range is set to, so the clip runs
  from 0.5 to 0.5 + semitones / 96.
- fade_in: a Fruity Balance's volume rises from silence to 0 dB over `bars` bars before the moment (a sub that comes in for the drop).
- gap: a Fruity Balance's volume drops to silence for the last `beats` beats before the moment (the hole before a drop).
- lowpass_open: a low-pass (the reference's Love Philter from its mid bass, cutoff knob 9) opens from 16% to fully open over `bars` bars into the
  moment, as the reference opens its bass over its buildup.
- lowpass_dip: the low-pass closes to 35% over the last `bars` bars and snaps open on the moment (the reference's vocal chop before its drop).
- filter_wobble: from the moment on, for `bars` bars, the low-pass cutoff swings from `low` to open once per `period` beats; one short clip
  placed again and again, as the reference repeats a one-beat filter clip 64 times on its lead.
- stutter_fill, reverse_fill, tape_stop: the reference's vocal chop Gross Beat switched to one of its time slots for the last `bars` bar(s) before
  the moment (plugins/grossbeat_vc_bank.json, measured: slot 4 repeats beats 2 to 4, slot 8 reverses the last beat, slot 18 stops the last beat
  like a tape), then back to Empty (slot 0 passes the sound unchanged). The bar must start on a bar line.
- fx_swell: a Fruity Flanger (the reference's drum-bus flanger) fades in over the last `beats` beats before the moment and out on it, its dry
  level dipping 3 dB, as the reference switches its drum-bus flanger in for transitions with a macro. Put it on the drum bus.

Settings for the inserted plugins come from the effect library. The clip shapes are written fresh; check each on a render around the moment
(measure_section_levels, measure_band_energy).
"""
from __future__ import annotations

import json

from . import fxlib
from .automation import (PLUGIN_PARAM_BASE, TICKS_PER_BEAT, add_automation_clip, channel_link, db_to_fader, mixer_link, next_channel_id,
                         place_clip_copies)
from .flpfile import Flp, FlpError
from .pump import first_free_row

LOWPASS = ("fh FutureBass Fruity Love Philter", "Fruity Love Philter", 9)
GROSS_BEAT = ("fh Vocal Chop Gross Beat", "Gross Beat", 0, "Transition Gross Beat")
GB_SLOTS = 35  # a time-slot clip value is slot / 35 (the reference's own clips: 9/35 and 10/35)
FILL_SLOT = {"stutter_fill": 4, "reverse_fill": 8, "tape_stop": 18}
# recipe: (library entry, plugin, knob, slot name)
PLUGINS = {"filter_sweep": ("fh Sidechain Fruity Filter", "Fruity Filter", 0, "Transition Filter"),
           "reverb_throw": ("fh Sidechain Fruity Reeverb 2", "Fruity Reeverb 2", 12, "Throw Reverb"),
           "fade_in": ("fh master Fruity Balance", "Fruity Balance", 1, "Fade Gain"), "gap": ("fh master Fruity Balance", "Fruity Balance", 1, "Gap Gain"),
           "lowpass_open": LOWPASS + ("Transition Lowpass",), "lowpass_dip": LOWPASS + ("Transition Lowpass",),
           "filter_wobble": LOWPASS + ("Wobble Lowpass",),
           "stutter_fill": GROSS_BEAT, "reverse_fill": GROSS_BEAT, "tape_stop": GROSS_BEAT, "fx_swell": ("fh Drum Group Fruity Flanger", "Fruity Flanger", 10, "Transition Flanger")}
SECOND = {"reverb_throw": 10, "fx_swell": 9}  # a dry-level clip goes with these
# Knob values to hold from the song start when the plugin's saved state is not neutral: before its first clip FL plays a plugin as saved, and the
# reference's flanger is saved at wet -7 dB, so without this it flanges everything until the first swell (measured 2026-10-25).
INIT = {"fx_swell": {10: 0.0, 9: 0.8}}
BEAT_RECIPES = ("reverb_throw", "gap", "fx_swell")
RECIPES = tuple(PLUGINS) + ("pitch_rise",)
# Where the high-pass sweep rests. The reference parks it at 0, which "passes everything", but at 0 the filter holds whatever offset it had
# when the cutoff came back down: renders of house, techno, dnb and trap kept a DC offset after the song ended and ran 33 s long (2026-10-25).
# Measured on the house remix (tools/calibrate_filter_rest.py, sandbox\diag\filter_rest): rest 0 held [0.0087, 0.0032] and rendered 250.65 s
# for 216.77 s of bars; rest 0.01 held nothing, rendered 220.65 s (a 3.9 s reverb tail) and left the drops' sub and bass within 0.01 dB.
FILTER_REST = 0.01
FLANGER_WET = 0.4426  # the reference's drum-bus flanger wet (-7.1 dB); its dry knob 0.7 is -3.1 dB, 0.8 is 0 dB


def moment_beat(f: Flp, at) -> float:
    """Beat of a moment: a marker name (first match, case-insensitive) or a bar number (1 is the first bar)."""
    if isinstance(at, (int, float)):
        if at < 1:
            raise FlpError("bars count from 1")
        return (float(at) - 1) * 4
    for m in f.time_markers():
        if (m["name"] or "").lower() == str(at).lower():
            return m["pos"] / TICKS_PER_BEAT
    raise FlpError("no time marker named %r in the current arrangement" % at)


def _slot_for(f: Flp, insert: int, recipe: str) -> int:
    """The slot holding this job's own plugin (found by slot name), else a free slot with the library entry put in and named (a filter early
    in the chain, the rest last)."""
    entry, plugin, _p, job = PLUGINS[recipe]
    mine = fxlib.find_named_slot(f, insert, job)
    if mine is not None:
        return mine
    free = [s for s in range(10) if fxlib.slot_plugin(f, insert, s) is None]
    if not free:
        raise FlpError("insert %d has no free slot for %s" % (insert, plugin))
    slot = free[0] if recipe == "filter_sweep" else free[-1]
    fxlib.inject(f, insert, slot, neutral(recipe, fxlib.load_entry(entry)))
    fxlib.set_slot_name(f, insert, slot, job)
    for knob, value in INIT.get(recipe, {}).items():
        add_automation_clip(f, next_channel_id(f), "%s Init" % job, mixer_link(insert, PLUGIN_PARAM_BASE + knob, sub=slot), [(0.0, value), (0.5, value)],
                            start_beat=0.0, track=first_free_row(f))
    return slot


FLANGER_STATE = {"dry": (10, 4000), "wet": (11, 0)}  # int32 positions in the Fruity Flanger state (after its version word): dry 0.8 is 0 dB, wet 0 is off


def neutral(recipe: str, entry: dict) -> dict:
    """A transition plugin saved so it passes the sound unchanged. FL plays a plugin as saved wherever no clip drives it, which includes every
    playback started past the init clip at bar 1: the drum-bus flanger saved at -7 dB wet flanged the whole techno remix while the person
    worked on it, and they switched it off as "too persistent and distracting" (2026-10-26)."""
    if recipe != "fx_swell":
        return entry
    import struct
    out = json.loads(json.dumps(entry))
    for ev in out["events"]:
        if ev[0] == 213:
            v = bytearray(bytes.fromhex(ev[1]))
            for _name, (k, raw) in FLANGER_STATE.items():
                if len(v) >= 4 * (k + 1):
                    v[4 * k:4 * k + 4] = struct.pack("<i", raw)
            ev[1] = bytes(v).hex()
    return out


PITCH_SPAN = 48.0  # semitones from the centre of a channel pitch clip to its top (measured, see the module text)


def _shape(recipe: str, start: float, end: float, semitones: float = 12.0) -> list[tuple]:
    """Points (absolute beats) for a recipe running from `start` to the moment `end`."""
    if recipe == "filter_sweep":
        return [(start, FILTER_REST), (end - 0.02, 0.42), (end, FILTER_REST), (end + 1, FILTER_REST)]
    if recipe == "reverb_throw":
        return [(start, 0.0), (end - 0.02, 1.0), (end, 0.0), (end + 1, 0.0)]
    if recipe == "pitch_rise":
        top = 0.5 + max(-PITCH_SPAN, min(PITCH_SPAN, semitones)) / (2 * PITCH_SPAN)
        return [(start, 0.5), (end - 0.02, top), (end, 0.5), (end + 1, 0.5)]
    if recipe == "fade_in":
        return [(start, 0.0), (end, db_to_fader(0.0)), (end + 1, db_to_fader(0.0))]
    if recipe == "gap":
        return [(start - 0.02, db_to_fader(0.0)), (start, 0.0), (end, db_to_fader(0.0)), (end + 1, db_to_fader(0.0))]
    if recipe == "lowpass_open":
        return [(start, 0.16), (end, 1.0), (end + 1, 1.0)]
    if recipe == "lowpass_dip":
        return [(start, 1.0), (end - 0.02, 0.35), (end, 1.0), (end + 1, 1.0)]
    if recipe == "fx_swell":
        return [(start, 0.0), (end - 0.02, FLANGER_WET), (end, 0.0), (end + 1, 0.0)]
    if recipe in FILL_SLOT:
        v = FILL_SLOT[recipe] / GB_SLOTS
        return [(start, v), (end - 0.01, v), (end, 0.0), (end + 1, 0.0)]
    raise FlpError("unknown recipe %r (known: %s)" % (recipe, ", ".join(RECIPES)))


def _dry(recipe: str, start: float, end: float) -> list[tuple]:
    """The dry-level clip that goes with a throw (100% dipping to 82%) or a flanger swell (0 dB dipping to -3.1 dB)."""
    normal, low = (0.8, 0.656) if recipe == "reverb_throw" else (0.8, 0.7)
    return [(start, normal), (end - 0.02, low), (end, normal), (end + 1, normal)]


def wobble_points(period: float, low: float) -> list[tuple]:
    """One period of the wobble: closed at the start, open at the end (a saw that opens, like the reference's one-beat clip). It ends open:
    FL holds a knob at a clip's last value, and a clip ending closed left the part filtered after the wobble (measured 2026-10-25)."""
    return [(0.0, low), (period * 0.98, 1.0), (period, 1.0)]


def add_wobble(f: Flp, at, row: int, insert: int, bars: float = 4, period: float = 1.0, low: float = 0.4) -> dict:
    """filter_wobble: one clip of one period, placed every `period` beats for `bars` bars from the moment."""
    start = moment_beat(f, at)
    if insert < 1 or period <= 0 or not 0 <= low < 1:
        raise FlpError("filter_wobble needs a mixer insert, a period above 0 and a low point below 1")
    slot = _slot_for(f, insert, "filter_wobble")
    ch = next_channel_id(f)
    add_automation_clip(f, ch, "Filter Wobble %s" % at, mixer_link(insert, PLUGIN_PARAM_BASE + PLUGINS["filter_wobble"][2], sub=slot),
                        wobble_points(period, low), start_beat=start, track=row)
    n = int(round(bars * 4 / period))
    place_clip_copies(f, ch, [start + k * period for k in range(1, n)], row)
    return {"insert": insert, "slot": slot, "recipe": "filter_wobble", "clip": ch, "start_beat": round(start, 2), "copies": n}


def add_transition(f: Flp, recipe: str, at, row: int, insert: int = -1, channel: int = -1, bars: float = 4, beats: float = 2, semitones: int = 12,
                   period: float = 1.0, low: float = 0.4) -> dict:
    if recipe == "filter_wobble":
        return add_wobble(f, at, row, insert, bars, period, low)
    end = moment_beat(f, at)
    length = beats if recipe in BEAT_RECIPES else bars * 4
    if recipe in FILL_SLOT and ((end - length) % 4 or length % 4):
        raise FlpError("%s needs whole bars on bar lines" % recipe)
    start = max(0.0, end - length)
    if end - start < 0.25:
        raise FlpError("the moment is too close to the start of the song for a %s" % recipe)
    pts = _shape(recipe, start, end, semitones)
    clip_start, rel = pts[0][0], [(b - pts[0][0], v) for b, v in pts]
    if recipe == "pitch_rise":
        if channel < 0 or channel not in f.channel_ids():
            raise FlpError("pitch_rise needs a channel that exists")
        link, bipolar, where = channel_link(channel, 4), True, {"channel": channel, "semitones": int(semitones)}
    else:
        if insert < 1:
            raise FlpError("%s needs a mixer insert (1 or higher)" % recipe)
        slot = _slot_for(f, insert, recipe)
        link, bipolar, where = mixer_link(insert, PLUGIN_PARAM_BASE + PLUGINS[recipe][2], sub=slot), False, {"insert": insert, "slot": slot}
    ch = next_channel_id(f)
    add_automation_clip(f, ch, "%s %s" % (recipe.replace("_", " ").title(), at), link, rel, start_beat=clip_start, track=row, bipolar=bipolar)
    out = dict(where, recipe=recipe, clip=ch, start_beat=round(clip_start, 2), moment_beat=round(end, 2))
    if recipe in SECOND:
        dry = _dry(recipe, start, end)
        ch2 = next_channel_id(f)
        add_automation_clip(f, ch2, "%s Dry %s" % (recipe.replace("_", " ").title(), at), mixer_link(insert, PLUGIN_PARAM_BASE + SECOND[recipe], sub=where["slot"]),
                            [(b - dry[0][0], v) for b, v in dry], start_beat=dry[0][0], track=row)
        out["dry_clip"] = ch2
    return out
