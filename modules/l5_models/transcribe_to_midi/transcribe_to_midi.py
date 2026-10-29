from __future__ import annotations

from pathlib import Path

from coproducer import call
from coproducer.result import Result, fail, ok


def _to_beats(events: list, bpm: float) -> list:
    scale = bpm / 60.0
    return [{"pitch": e["pitch"], "start": round(e["start"] * scale, 4), "duration": round(max(0.01, e["end"] - e["start"]) * scale, 4),
             "velocity": max(1, min(127, round(e["velocity"] * 127)))} for e in events]


def transcribe_to_midi(input_path: str, tempo_bpm: float = 120.0, onset_threshold: float = 0.5, frame_threshold: float = 0.3,
                       min_note_ms: float = 127.7, out_midi_path: str = "") -> Result:
    """Transcribe audio to notes with Basic Pitch. Notes are in beats at tempo_bpm: {pitch, start, duration, velocity}.

    With out_midi_path the notes are also written as a MIDI file inside the sandbox. Run it on a separated stem, not a full mix.
    """
    if not Path(input_path).is_file():
        return fail("E_NOT_FOUND", "no audio file at %s" % Path(input_path).name)
    got = call("run_model_op", model="basicpitch", op="transcribe", timeout_s=900,
               args={"input_path": input_path, "onset_threshold": onset_threshold, "frame_threshold": frame_threshold, "min_note_ms": min_note_ms})
    if not got.ok:
        return got
    notes = _to_beats(got.value["notes"], tempo_bpm)
    if out_midi_path:
        wrote = call("write_midi_file", notes=notes, path=out_midi_path, tempo_bpm=tempo_bpm)
        if not wrote.ok:
            return wrote
    return ok({"notes": notes, "count": len(notes), "tempo_bpm": tempo_bpm, "midi_path": out_midi_path or None})
