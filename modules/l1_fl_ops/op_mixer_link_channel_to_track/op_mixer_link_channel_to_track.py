import mixer


def op_mixer_link_channel_to_track(channel: int, track: int, select: bool = False) -> dict:
    """Run mixer.linkChannelToTrack inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"channel": channel, "track": track, "select": select}, {"channel": "i", "track": "i", "select": "b"})
    if bad:
        return bad
    return _run(mixer.linkChannelToTrack, channel, track, select)
