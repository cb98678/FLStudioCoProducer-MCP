"""vocalclips: onset search and the trim/snap plan on synthetic clips."""
import struct

import numpy as np

from coproducer import vocalclips as V
from coproducer.flpfile import Flp, PLAYLIST_ITEM_SIZE

SR = 48000
TICK = V.ms_per_tick(140)


def _item(pos, ref, length, s, e):
    b = bytearray(PLAYLIST_ITEM_SIZE)
    struct.pack_into("<I", b, 0, pos)
    struct.pack_into("<H", b, 4, 0x5000)
    struct.pack_into("<H", b, 6, ref)
    struct.pack_into("<I", b, 8, length)
    struct.pack_into("<ff", b, 24, s, e)
    return bytes(b)


def _burst_env(at_ms, dur_ms=300, total_ms=2000):
    x = np.zeros(int(total_ms / 1000 * SR))
    i0 = int(at_ms / 1000 * SR)
    t = np.arange(int(dur_ms / 1000 * SR)) / SR
    x[i0:i0 + len(t)] = 0.5 * np.sin(2 * np.pi * 300 * t)
    return V.envelope(x, SR)


def test_onset_found_within_a_few_ms():
    env = _burst_env(500)
    on = V.onset_in_window(env, SR, 0, 1500)
    assert 495 <= on <= 505
    assert V.onset_in_window(env, SR, 1200, 1900) is None


def test_item_roundtrip_keeps_other_bytes():
    it = _item(384, 98, 100, 1000.0, 1500.0)
    out = V.write_item(it, pos=390, start_ms=1010.0)
    assert V.read_item(out)["pos"] == 390 and V.read_item(out)["start_ms"] == 1010.0
    assert out[8:24] == it[8:24] and out[28:] == it[28:]


def test_lead_in_is_trimmed_and_speed_is_unchanged():
    env = _burst_env(580)                      # the word starts 80 ms into a clip that starts at 500 ms
    n = int(round(500 / TICK))
    it = _item(384, 98, n, 500.0, 1000.0)
    p = V.plan_clip(it, env, SR)
    assert p.trimmed_ms > 60
    assert abs((p.end_ms - p.start_ms) - 500.0) < 0.01          # same window length, same speed
    assert p.moved_ticks == 0 and abs(p.grid_err_ms) < 12


def test_late_clip_snaps_onto_the_sixteenth_grid():
    env = _burst_env(500)
    n = int(round(300 / TICK))
    pos = 384 + 6                               # 6 ticks (26.8 ms) after the 16th line
    it = _item(pos, 98, n, 500.0, 800.0)
    p = V.plan_clip(it, env, SR)
    assert p.moved_ticks == -6 and p.pos == 384
    assert abs(p.grid_err_ms) < 3


def test_source_shift_is_applied():
    env = _burst_env(300)                       # cleaned file starts 200 ms later than the offsets assume
    n = int(round(300 / TICK))
    it = _item(384, 98, n, 500.0, 800.0)
    p = V.plan_clip(it, env, SR, source_shift_ms=200.0)
    assert abs(p.start_ms - 300.0) < 5 and abs(p.lag_ms) < 12


def test_map_playlist_rewrites_items(tmp_path):
    from coproducer.flpfile import EV_PLAYLIST
    f = Flp(b"FLhd" + bytes(10) + b"\x00\x00", [[EV_PLAYLIST, _item(0, 98, 10, 0.0, 10.0) + _item(100, 98, 10, 0.0, 10.0)]], b"")
    changed = f.map_playlist(lambda it: V.write_item(it, pos=V.read_item(it)["pos"] + 1))
    assert changed == 2
    assert [V.read_item(i)["pos"] for i in f.playlist_items()] == [1, 101]


def test_whole_end_never_runs_into_the_next_word_and_keeps_a_held_note():
    from coproducer import remixaudio
    rate = 16000
    t = np.arange(int(3.0 * rate)) / rate
    x = np.zeros_like(t)
    a = (t > 0.2) & (t < 1.6)
    x[a] = 0.2 * np.sin(2 * np.pi * 330 * t[a])                  # the last word, held to 1.6 s
    b = (t >= 1.6) & (t < 2.6)
    x[b] = 0.2 * np.sin(2 * np.pi * 262 * t[b])                  # the next word, sung straight on (no gap)
    x = x.astype("float32")
    e = remixaudio.whole_end(x, rate, 2.7, "phrase", "okay", next_t=1.6, hint=0.8)   # a gap snap ran past the next word
    assert 1.5 <= e <= 1.6, e
    e = remixaudio.whole_end(x, rate, 0.8, "phrase", "okay", next_t=1.6, hint=0.8)   # the recogniser ended the held word early
    assert 1.5 <= e <= 1.6, e
    x[(t >= 1.6) & (t < 1.9)] = 0.0                              # a breath before the next word: the end stays where the voice stops
    x[(t >= 1.9)] = 0.0
    e = remixaudio.whole_end(x, rate, 1.62, "phrase", "okay", next_t=2.4, hint=1.5)
    assert e < 1.75, e
