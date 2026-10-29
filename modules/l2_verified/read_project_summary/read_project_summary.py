from __future__ import annotations

from coproducer import call
from coproducer.result import Result, first_error, ok


def read_project_summary() -> Result:
    """Return counts of mixer tracks, channels, patterns that hold data (FL counts only non-default ones) and playlist tracks, plus tempo and project name.

    Errors: any bridge or FL error from the reads.
    """
    tracks = call("op_mixer_track_count")
    channels = call("op_channels_channel_count")
    patterns = call("op_patterns_pattern_count")
    playlist = call("op_playlist_track_count")
    tempo = call("op_mixer_get_current_tempo", asInt=True)
    title = call("op_ui_get_prog_title")
    bad = first_error(tracks, channels, patterns, playlist, tempo, title)
    if bad:
        return bad
    return ok({"project": title.value, "mixer_tracks": tracks.value, "channels": channels.value,
               "patterns_with_data": patterns.value, "playlist_tracks": playlist.value, "tempo": tempo.value})
