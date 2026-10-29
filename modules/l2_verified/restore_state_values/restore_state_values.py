from __future__ import annotations

from coproducer import call
from coproducer.result import Result, first_error, ok


def restore_state_values(snapshot: dict) -> Result:
    """Put tracks, channels and tempo back to the values in a snapshot, using verified writes.

    Stops at the first part that fails. Tempo is only written when it differs.
    """
    tracks = call("restore_track_values", snapshot=snapshot)
    channels = call("restore_channel_values", snapshot=snapshot) if "channels" in snapshot else ok({"applied": 0})
    cur = call("op_mixer_get_current_tempo", asInt=True)
    bad = first_error(tracks, channels, cur)
    if bad:
        return bad
    tempo = ok({"applied": 0}, verified=True)
    if "tempo" in snapshot and abs(cur.value - snapshot["tempo"]) > 0.01:
        tempo = call("set_tempo_verified", bpm=snapshot["tempo"])
        if not tempo.ok:
            return tempo
        tempo = ok({"applied": 1}, verified=True)
    n = tracks.value["applied"] + channels.value["applied"] + tempo.value["applied"]
    return ok({"applied": n}, verified=True)
