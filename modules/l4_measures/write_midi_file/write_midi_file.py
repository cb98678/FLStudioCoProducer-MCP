from __future__ import annotations

import mido

from coproducer import call
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def write_midi_file(notes: list[dict], path: str, tempo_bpm: float = 120.0, ppq: int = 480) -> Result:
    """Write a note list (beats) to a MIDI file inside the sandbox folder. Overwrites an existing file.

    Errors: E_SANDBOX_VIOLATION when path is outside the sandbox or no sandbox is configured.
    """
    root = get_service("sandbox_root")
    if root is None:
        return fail("E_SANDBOX_VIOLATION", "no sandbox folder is configured")
    chk = call("check_sandbox_path", path=path, sandbox_root=str(root))
    if not chk.ok:
        return chk
    events = []
    for n in notes:
        events.append((round(n["start"] * ppq), 1, n["pitch"], n.get("velocity", 100), n.get("channel", 0)))
        events.append((round((n["start"] + n["duration"]) * ppq), 0, n["pitch"], 0, n.get("channel", 0)))
    track, last = mido.MidiTrack([mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(tempo_bpm))]), 0
    for tick, on, pitch, vel, ch in sorted(events):
        track.append(mido.Message("note_on" if on else "note_off", note=pitch, velocity=vel, channel=ch, time=tick - last))
        last = tick
    mid = mido.MidiFile(ticks_per_beat=ppq)
    mid.tracks.append(track)
    mid.save(chk.value["resolved"])
    return ok({"path": chk.value["resolved"], "notes": len(notes)})
