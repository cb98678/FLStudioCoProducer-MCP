from __future__ import annotations

from coproducer import call
from coproducer.result import Result, first_error, ok


def snapshot_state(track_limit: int = 0, include_channels: bool = True) -> Result:
    """Capture mixer tracks, channels and tempo into one JSON-friendly snapshot for diffing and restoring.

    Plugin parameters are not included; capture those with get_plugin_param_by_name when needed.
    """
    tracks = call("snapshot_tracks", track_limit=track_limit)
    channels = call("snapshot_channels") if include_channels else ok({})
    tempo = call("op_mixer_get_current_tempo", asInt=True)
    bad = first_error(tracks, channels, tempo)
    if bad:
        return bad
    snap = {"tracks": tracks.value, "tempo": tempo.value}
    if include_channels:
        snap["channels"] = channels.value
    return ok(snap)
