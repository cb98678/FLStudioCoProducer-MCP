from __future__ import annotations

import mido

from coproducer.result import Result, fail, ok


def _track_notes(track, ppq: int) -> tuple[list, dict]:
    """Notes of one track in beats, plus any tempo and time signature found."""
    notes, found, open_, tick = [], {}, {}, 0
    for msg in track:
        tick += msg.time
        if msg.type == "set_tempo":
            found.setdefault("tempo", round(mido.tempo2bpm(msg.tempo), 3))
        elif msg.type == "time_signature":
            found.setdefault("sig", [msg.numerator, msg.denominator])
        elif msg.type == "note_on" and msg.velocity > 0:
            open_[(msg.channel, msg.note)] = (tick, msg.velocity)
        elif msg.type in ("note_off", "note_on") and (msg.channel, msg.note) in open_:
            t0, vel = open_.pop((msg.channel, msg.note))
            notes.append({"pitch": msg.note, "start": t0 / ppq, "duration": max(1, tick - t0) / ppq,
                          "velocity": vel, "channel": msg.channel})
    return notes, found


def read_midi_file(path: str) -> Result:
    """Read a MIDI file into a note list in beats, with ticks per beat, the first tempo and time signature.

    Notes: {pitch, start, duration, velocity, channel}. Channel 9 (zero based) is the General MIDI drum channel.
    """
    try:
        mid = mido.MidiFile(path)
    except (OSError, ValueError, EOFError, KeyError) as e:
        return fail("E_IO", "cannot read MIDI file: %s" % e)
    notes, tempo, sig = [], 120.0, [4, 4]
    for track in mid.tracks:
        got, found = _track_notes(track, mid.ticks_per_beat)
        notes += got
        tempo, sig = found.get("tempo", tempo), found.get("sig", sig)
    notes.sort(key=lambda n: (n["start"], n["pitch"]))
    return ok({"notes": notes, "ppq": mid.ticks_per_beat, "tempo_bpm": tempo, "time_signature": sig,
               "length_beats": max((n["start"] + n["duration"] for n in notes), default=0.0)})
