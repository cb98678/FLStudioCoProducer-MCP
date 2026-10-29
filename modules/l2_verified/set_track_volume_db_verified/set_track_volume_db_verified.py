from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, first_error, ok

# Fader position and dB measured on FL 26.1.7 (docs/FL_API_FINDINGS.md). The law is not 20*log10(v/0.8), so these points give the first guess.
_LAW = ((0.25, -19.05), (0.5, -9.18), (0.8, 0.0), (1.0, 5.59))


def _first_guess(db: float) -> float:
    if db <= _LAW[0][1]:
        return max(0.02, _LAW[0][0] * 10 ** ((db - _LAW[0][1]) / 20))
    for (v0, d0), (v1, d1) in zip(_LAW, _LAW[1:]):
        if db <= d1:
            return v0 + (v1 - v0) * (db - d0) / (d1 - d0)
    return 1.0


def _next_guess(points: list, db: float) -> float | None:
    (v0, d0), (v1, d1) = points[-2], points[-1]
    if abs(d1 - d0) < 1e-9 or abs(v1 - v0) < 1e-12:
        return None
    return min(1.0, max(0.0, v1 + (db - d1) * (v1 - v0) / (d1 - d0)))


def set_track_volume_db_verified(index: int, db: float) -> Result:
    """Set a mixer track's fader to a level in dB and confirm by reading the dB value back.

    Starts from a guess interpolated from the measured fader law, then refines with the secant method, at most five writes.
    Errors: E_NOT_VERIFIED when the readback stays more than 0.15 dB away (for example above the fader's top).
    """
    cur_v = call("op_mixer_get_track_volume", index=index)
    cur_db = call("op_mixer_get_track_volume", index=index, mode=1)
    bad = first_error(cur_v, cur_db)
    if bad:
        return bad
    points, v, got = [(cur_v.value, cur_db.value)], _first_guess(db), cur_db.value
    for n in range(1, 6):
        w = call("op_mixer_set_track_volume", index=index, volume=v)
        r = call("op_mixer_get_track_volume", index=index, mode=1) if w.ok else w
        if not r.ok:
            return r
        got = r.value
        if abs(got - db) <= 0.15:
            return ok(got, verified=True, volume=v, writes=n)
        points.append((v, got))
        v = _next_guess(points, db)
        if v is None:
            break
    return fail("E_NOT_VERIFIED", "fader reads %.2f dB, wanted %.2f dB" % (got, db), wanted=db, read=got)
