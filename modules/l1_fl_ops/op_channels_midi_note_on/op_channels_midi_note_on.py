import channels


def op_channels_midi_note_on(indexGlobal: int, note: int, velocity: int, channel: int = -1) -> dict:
    """Run channels.midiNoteOn inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"indexGlobal": indexGlobal, "note": note, "velocity": velocity, "channel": channel}, {"indexGlobal": "i", "note": "i", "velocity": "i", "channel": "j"})
    if bad:
        return bad
    return _run(channels.midiNoteOn, indexGlobal, note, velocity, channel)
