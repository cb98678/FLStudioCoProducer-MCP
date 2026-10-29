"""Editable risers and transition synths: 3x Osc patches from the effect library (the Future House reference's own noise patches and its transition
stab), each added as a channel with one pattern placed around a section change. They replace rendered FX audio with something the person can open
and change in FL.

- noise_riser: band-pass noise whose level and pitch rise over the note; the note ends on the moment (the reference's runs 3 bars).
- noise_downlifter: band-pass noise that falls away over the note; the note starts on the moment (the reference's runs 4 bars).
- impact_synth: a one-beat chord with a falling pitch on the moment, voiced from the key the way the reference voices it (root, octave, fifth
  above that, two octaves, third and fifth on top).

The patch's own envelopes set the shape and the note length sets how long it lasts; the reference ran at 126 BPM, so a patch whose envelope is set in
time, not beats, can finish a little early or late at another tempo. The channels keep the reference's levels, which are quiet in our mix (on
the tech-house remix the riser's loudest beat measured about -40 dB RMS solo, 2026-10-25): set their level with gain staging, or pass a volume.
Check the result on a render around the moment (measure_band_energy).
"""
from __future__ import annotations

from . import drumtune, flporg, fxlib, partmix, transitions
from .flpfile import TICKS_PER_BEAT, Flp, FlpError, note_bytes

PATCHES = {"noise_riser": ("fh noise riser", "Noise Riser", 4), "noise_downlifter": ("fh noise downlifter", "Noise Downlifter", 4),
           "impact_synth": ("fh impact stab", "Impact Synth", 0)}
NOISE_KEY = 48  # the reference plays its noise patches on C4
STAB_MAJOR, STAB_MINOR = (0, 12, 19, 24, 28, 31), (0, 12, 19, 24, 27, 31)


def fx_insert(f: Flp) -> int:
    """The mixer insert the project's FX channels use (the first one named as FX), else the master."""
    for ch in f.channel_ids():
        info = f.channel_info(ch)
        if partmix.role_of(info["name"] or "") == "fx" and info["track"]:
            return info["track"]
    return 0


def chord(key: str) -> list[int]:
    """The stab's notes for a key: the root between C3 and B3 (keys 36 to 47), voiced like the reference."""
    root = 36 + drumtune.key_pc(key)
    minor = any(w in key.lower().split() for w in ("minor", "min")) or key.strip().endswith("m")
    return [root + i for i in (STAB_MINOR if minor else STAB_MAJOR)]


def _span(kind: str, moment: float, bars: float) -> tuple[float, float]:
    """(start beat, length in beats) of the note."""
    if kind == "noise_riser":
        return moment - bars * 4, bars * 4
    if kind == "noise_downlifter":
        return moment, bars * 4
    return moment, 1.0


def add_fx_synth(f: Flp, kind: str, at, row: int, insert: int = -1, bars: float = 0, key: str = "A", volume: int | None = None) -> dict:
    if kind not in PATCHES:
        raise FlpError("unknown transition synth %r (known: %s)" % (kind, ", ".join(PATCHES)))
    entry, label, default_bars = PATCHES[kind]
    moment = transitions.moment_beat(f, at)
    start, length = _span(kind, moment, bars or default_bars or 1)
    if start < 0 or start % 4 or length <= 0:
        raise FlpError("%s at %r needs whole bars after the song start (starts on beat %g)" % (kind, at, start))
    ch = max(f.channel_ids()) + 1
    track = fx_insert(f) if insert < 0 else insert
    fxlib.add_channel(f, fxlib.load_entry(entry), ch, "%s %s" % (label, at), track=track)
    if volume is not None:
        f.set_channel_volume_raw(ch, volume)
    try:
        flporg.set_channel_group(f, ch, flporg.set_display_groups(f, ["FX"])["FX"])
    except FlpError:
        pass
    keys = chord(key) if kind == "impact_synth" else [NOISE_KEY]
    notes = b"".join(note_bytes(0, ch, k, int(length * TICKS_PER_BEAT), 104 if kind != "impact_synth" else 100) for k in keys)
    pid = f.next_pattern_id(1)
    f.add_pattern(pid, "%s %s" % (label, at), notes)
    f.add_playlist_clips([(pid, int(start // 4), max(1, int(-(-length // 4))), row)])
    return {"kind": kind, "channel": ch, "insert": track, "pattern": pid, "start_bar": int(start // 4) + 1, "bars": length / 4, "notes": keys}
