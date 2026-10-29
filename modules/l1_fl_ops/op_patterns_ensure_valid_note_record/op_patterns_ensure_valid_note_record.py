import patterns


def op_patterns_ensure_valid_note_record(index: int, playNow: int = 0) -> dict:
    """Run patterns.ensureValidNoteRecord inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "playNow": playNow}, {"index": "i", "playNow": "i"})
    if bad:
        return bad
    return _run(patterns.ensureValidNoteRecord, index, playNow)
