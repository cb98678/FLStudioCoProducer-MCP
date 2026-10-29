from __future__ import annotations

from pathlib import Path

from coproducer import call, melody
from coproducer.result import Result, fail, ok


def transcribe_vocal_melody(path: str, offset_s: float = 0.0, duration_s: float = 0.0, min_conf: float = 0.5, out_midi_path: str = "",
                            bpm: float = 120.0) -> Result:
    """The sung melody of a separated vocal stem as notes {start, end, pitch, cents, velocity} in seconds of the file, from torchcrepe pitch (MIT,
    mir environment). Also a key estimate from the notes alone, an independent check on estimate_key_dsp: on the Friends chorus it read E major
    with A major a close second, so trust it only together with the bass roots. With out_midi_path the notes go into a MIDI file at bpm.

    Errors: E_NOT_FOUND, E_MODEL, E_NOT_VERIFIED (no voiced notes), E_SANDBOX_VIOLATION (MIDI path outside the sandbox).
    """
    if not Path(path).is_file():
        return fail("E_NOT_FOUND", "no audio file at %s" % Path(path).name)
    args = {"path": path, "offset_s": offset_s}
    if duration_s:
        args["duration_s"] = duration_s
    got = call("run_model_op", model="mir", op="melody", timeout_s=1800, args=args)
    if not got.ok:
        return got
    v = got.value
    notes = melody.notes_from_f0(v["f0"], v["periodicity"], v["rms"], v["hop_s"], v["offset_s"], min_conf=min_conf)
    if not notes:
        return fail("E_NOT_VERIFIED", "no voiced notes found (is this a vocal stem?)")
    out = {"notes": notes, "key": melody.key_from_notes(notes), "count": len(notes), "range": [min(n["pitch"] for n in notes), max(n["pitch"] for n in notes)]}
    if out_midi_path:
        t0 = notes[0]["start"]
        mid = call("write_midi_file", notes=melody.to_beats(notes, lambda t: (t - t0) * bpm / 60.0), path=out_midi_path, tempo_bpm=bpm)
        if not mid.ok:
            return mid
        out["midi"] = out_midi_path
    return ok(out, verified=True)
