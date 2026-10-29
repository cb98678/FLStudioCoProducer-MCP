import general


def op_general_dump_score_log(time: int, silent: bool = False) -> dict:
    """Run general.dumpScoreLog inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"time": time, "silent": silent}, {"time": "i", "silent": "b"})
    if bad:
        return bad
    return _run(general.dumpScoreLog, time, silent)
