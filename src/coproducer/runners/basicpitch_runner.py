"""Basic Pitch audio to notes. Runs inside the basicpitch environment (pip install basic-pitch; Python 3.7 to 3.11).

Docs checked 2026-10-18: https://github.com/spotify/basic-pitch and basic_pitch/inference.py (predict signature).
predict() returns (model_output, midi_data, note_events); each note event is
(start_time_s, end_time_s, pitch_midi, amplitude, pitch_bends or None).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner_common import serve  # noqa: E402


def to_notes(events: list) -> list[dict]:
    """Convert Basic Pitch note events to {start, end, pitch, velocity} in seconds, velocity 0 to 1."""
    out = []
    for e in events:
        out.append({"start": round(float(e[0]), 4), "end": round(float(e[1]), 4), "pitch": int(e[2]),
                    "velocity": round(min(1.0, max(0.0, float(e[3]))), 3)})
    return sorted(out, key=lambda n: (n["start"], n["pitch"]))


def transcribe(a: dict) -> dict:
    from basic_pitch.inference import predict
    _, _, events = predict(a["input_path"], onset_threshold=a.get("onset_threshold", 0.5), frame_threshold=a.get("frame_threshold", 0.3),
                           minimum_note_length=a.get("min_note_ms", 127.7), minimum_frequency=a.get("min_hz"),
                           maximum_frequency=a.get("max_hz"), multiple_pitch_bends=False, melodia_trick=a.get("melodia_trick", True))
    return {"notes": to_notes(events)}


if __name__ == "__main__":
    serve({"load": lambda a: {"loaded": a.get("variant")}, "unload": lambda a: True, "ping": lambda a: "pong", "transcribe": transcribe})
