"""Audio-clip timing: find where a chopped word really starts inside a playlist clip, and nudge the clip onto the grid.

An FL audio clip item stores its content window as two float32 values in milliseconds (start offset at byte 24, end offset at 28)
and its length in ticks at byte 8, so the playback rate is (end - start) / (length_ticks * ms_per_tick). Moving the start and end
together slides the content under the clip without changing its speed; moving `pos` slides the clip on the grid.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass

import numpy as np

ITEM_POS = 0
ITEM_REF = 6
ITEM_LEN = 8
ITEM_START = 24
ITEM_END = 28
PATTERN_BASE = 20480


def ms_per_tick(bpm: float, ppq: int = 96) -> float:
    return 60000.0 / bpm / ppq


def read_item(it: bytes) -> dict:
    pos, = struct.unpack_from("<I", it, ITEM_POS)
    ref, = struct.unpack_from("<H", it, ITEM_REF)
    ln, = struct.unpack_from("<I", it, ITEM_LEN)
    s, e = struct.unpack_from("<ff", it, ITEM_START)
    return {"pos": pos, "ref": ref, "len": ln, "start_ms": s, "end_ms": e}


def write_item(it: bytes, *, pos: int | None = None, start_ms: float | None = None, end_ms: float | None = None) -> bytes:
    b = bytearray(it)
    if pos is not None:
        struct.pack_into("<I", b, ITEM_POS, int(pos))
    if start_ms is not None:
        struct.pack_into("<f", b, ITEM_START, start_ms)
    if end_ms is not None:
        struct.pack_into("<f", b, ITEM_END, end_ms)
    return bytes(b)


def is_audio_clip(it: bytes) -> bool:
    d = read_item(it)
    return d["ref"] < PATTERN_BASE and d["len"] > 0


def envelope(x: np.ndarray, sr: int, win_ms: float = 3.0) -> np.ndarray:
    k = max(1, int(sr * win_ms / 1000))
    return np.sqrt(np.convolve(x.astype(np.float64) ** 2, np.ones(k) / k, mode="same"))


def onset_in_window(env: np.ndarray, sr: int, start_ms: float, end_ms: float, rel: float = 0.08, floor_db: float = -38.0) -> float | None:
    """Milliseconds (in the source) where the sound first rises above max(rel * window peak, floor), or None if the window is silent."""
    i0 = max(0, int(start_ms / 1000 * sr))
    i1 = min(len(env), int(end_ms / 1000 * sr))
    seg = env[i0:i1]
    if len(seg) < 10 or seg.max() < 10 ** (floor_db / 20):
        return None
    thr = max(10 ** (floor_db / 20), rel * seg.max())
    return (i0 + int(np.argmax(seg > thr))) / sr * 1000.0


@dataclass
class ClipPlan:
    pos: int
    start_ms: float
    end_ms: float
    lag_ms: float          # where the sound starts inside the clip, in song time, before the plan
    grid_err_ms: float     # how far from the nearest grid line the onset ends up after the plan
    trimmed_ms: float
    moved_ticks: int


def plan_clip(it: bytes, env: np.ndarray, sr: int, *, bpm: float = 140.0, grid_steps_per_beat: int = 4, source_shift_ms: float = 0.0,
              trim_over_ms: float = 8.0, preroll_ms: float = 6.0, snap_over_ms: float = 12.0, snap_max_ms: float = 54.0) -> ClipPlan | None:
    """Decide the new pos/start/end for one clip. Two moves, in this order:
    1. lead-in over trim_over_ms is trimmed (start and end slide together, so the speed stays), keeping preroll_ms of attack;
    2. an onset that is still between snap_over_ms and snap_max_ms off the grid moves the clip onto the grid line.
    source_shift_ms is how much earlier the cleaned file starts than the one the offsets were written for; the returned
    start and end are already in the cleaned file's time.
    """
    d = read_item(it)
    tick = ms_per_tick(bpm)
    s, e = d["start_ms"] - source_shift_ms, d["end_ms"] - source_shift_ms
    rate = (e - s) / (d["len"] * tick)
    if rate <= 0:
        return None
    on = onset_in_window(env, sr, s, e)
    if on is None:
        return None
    lag = (on - s) / rate
    trimmed = 0.0
    if lag > trim_over_ms:
        trimmed = (on - preroll_ms * rate) - s          # source ms
        s, e = s + trimmed, e + trimmed
        lag = preroll_ms
    grid = 60000.0 / bpm / grid_steps_per_beat
    t_on = d["pos"] * tick + lag
    err = t_on - round(t_on / grid) * grid
    moved = 0
    if snap_over_ms <= abs(err) <= snap_max_ms:
        moved = int(round(-err / tick))
        err += moved * tick
    return ClipPlan(d["pos"] + moved, s, e, lag, err, trimmed, moved)
