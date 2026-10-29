"""Wavetables and sampler sounds from a song's own material (wavetables, serumspec; skill serum-wavetables, 2026-10-28): a held note
comes back as pitch-synchronous cycles with its own harmonic levels, bleed that does not repeat is averaged out, frames are phase
aligned, the table file is what Serum reads, serum-mcp's slicing leaves it nearly as written, formulas follow Serum's parser (and the
attachment's sub formula is shown not to be a sine), the sampler plan reads pitch and balance, and the spec parts assemble."""
from __future__ import annotations

import math

import numpy as np
import pytest

from coproducer import serumspec, wavetables

RATE = 48000


def note(f0, secs, levels, rate=RATE, phase=None, attack=0.004):
    t = np.arange(int(secs * rate)) / rate
    ph = phase if phase is not None else [0.3 * k for k in range(len(levels))]
    x = sum(a * np.sin(2 * np.pi * (k + 1) * f0 * t + ph[k]) for k, a in enumerate(levels))
    return x * np.minimum(1.0, t / attack)


def test_a_held_note_becomes_its_own_cycles():
    lv = [1.0, 0.5, 0.33, 0.25, 0.2, 0.0, 0.14]
    x = note(98.0, 0.8, lv)
    t = wavetables.cycles(x, RATE, frames=8)
    assert abs(t["f0_hz"] - 98.0) < 0.3 and t["note"] == "G2" and len(t["frames"]) == 8
    got = t["last"][:7]
    assert all(abs(g - want) < 0.03 for g, want in zip(got, lv)), got
    assert all(len(f) == wavetables.FRAME and abs(float(np.max(np.abs(f))) - wavetables.PEAK) < 1e-9 for f in t["frames"])
    assert t["edge_loss_db"] < -30


def test_bleed_that_does_not_repeat_is_averaged_out():
    lv = [1.0, 0.0, 0.4, 0.0, 0.2]
    clean = note(55.0, 1.0, lv)
    noisy = clean + np.random.default_rng(2).standard_normal(len(clean)) * 0.25
    one = wavetables.cycles(noisy, RATE, frames=4, periods=1, f0=55.0)
    many = wavetables.cycles(noisy, RATE, frames=4, periods=8, f0=55.0)
    ref = wavetables.cycles(clean, RATE, frames=4, periods=8, f0=55.0)["frames"][1]
    err = [float(np.sqrt(np.mean((t["frames"][1] - ref) ** 2))) for t in (one, many)]
    assert err[1] < 0.5 * err[0]


def test_frames_share_their_phase_so_they_morph_without_cancelling():
    """A note whose harmonics shift phase halfway (as a stem's partials drift): both frames of one table keep one fundamental phase."""
    a = note(110.0, 0.5, [1.0, 0.3, 0.2], phase=[0.0, 0.0, 0.0])
    b = note(110.0, 0.5, [1.0, 0.3, 0.2], phase=[2.0, 1.0, 0.5], attack=1e-9)
    t = wavetables.cycles(np.concatenate([a, b]), RATE, frames=2, f0=110.0)
    fa, fb = t["frames"]
    pa, pb = (np.angle(np.fft.rfft(f)[1]) for f in (fa, fb))
    assert abs(math.remainder(pa - pb, 2 * math.pi)) < 0.02
    mid = 0.5 * (fa + fb)                                  # what Serum plays between two frames
    assert np.sqrt(np.mean(mid ** 2)) > 0.6 * np.sqrt(np.mean(fa ** 2))


def test_the_table_file_is_serums_and_reads_back(tmp_path):
    frames = wavetables.formula("sin(pi*x)*(1-y) + y*sin(3*pi*x)", 4)["frames"]
    p = wavetables.write_table(tmp_path / "t.wav", frames)
    raw = p.read_bytes()
    assert raw[:4] == b"RIFF" and wavetables.CLM in raw and len(raw) > 4 * 2048 * 4
    back, clm = wavetables.read_table(p)
    assert clm and len(back) == 4 and np.allclose(back[2], frames[2], atol=1e-6)
    import soundfile as sf
    info = sf.info(str(p))
    assert info.samplerate == 44100 and info.channels == 1 and info.frames == 4 * 2048


def test_serum_mcp_slicing_falls_on_the_frames():
    """serum-mcp's sample_source picks slice starts by linspace(0, len - 2048, n): on a file of n frames they are the frame starts."""
    n = 16
    starts = np.linspace(0, (n - 1) * 2048, num=n).astype(int)
    assert list(starts) == [k * 2048 for k in range(n)]


def test_formulas_follow_serums_parser():
    sine = wavetables.formula("sin(pi*x)", 2)
    assert sine["first"][0] == 1.0 and max(sine["first"][1:]) < 1e-3 and sine["wrap_jump"] < 1e-9
    att = wavetables.formula("sin(x + y * sin(x * 2))", 2)          # the attachment's 'clean sub' at y = 0 is sin(x), x in radians -1..1
    assert att["wrap_jump"] > 1.5 and att["first"][1] > 0.3           # a third of a sine cycle, a saw-like jump: not a sub sine
    fixed = wavetables.formula("sin(pi*x + y*sin(2*pi*x))", 3)
    assert max(fixed["first"][1:]) < 1e-3                              # a sine at y = 0
    odd = fixed["last"]
    assert odd[2] > 0.1 and odd[1] < 1e-3 and odd[3] < 1e-3          # phase modulation by twice the frequency adds odd harmonics only
    cheb = wavetables.formula("cos(3*acos(x))", 1)                    # Chebyshev T3 on a ramp is a shaped saw, not the 3rd harmonic
    assert cheb["first"][1] > 0.1 and cheb["wrap_jump"] > 1.5
    with pytest.raises(wavetables.TableError):
        wavetables.formula("__import__('os')", 1)
    with pytest.raises(wavetables.TableError):
        wavetables.formula("sin(q)", 1)


def test_turning_a_formula_table_puts_the_wrap_where_it_is_quiet():
    t = wavetables.formula("cos(pi*x)", 1)["frames"]
    assert wavetables.edge_loss_db(wavetables.turn_quiet(t)) < wavetables.edge_loss_db(t) - 10


def test_sampler_plan_reads_pitch_balance_and_loop():
    x = note(110.0, 1.0, [1.0, 0.5, 0.2]) * 0.5
    st = np.stack([x, 0.5 * x], axis=1)
    p = wavetables.sampler_plan(st, RATE, "bass", "C:/sandbox/b.wav")
    assert abs(p["pitch_midi"] - 45.0) < 0.1 and p["play_note"] == 60 and abs(p["lr_balance_db"] - 6.02) < 0.05
    o = p["oscillator"]
    assert o["octave"] * 12 + o["semitone"] + o["fine"] / 100 == pytest.approx(15.0, abs=0.1)
    assert o["sample_loop"] == "forward" and 0 < o["sample_loop_start"] < o["sample_loop_end"] < 100
    v = wavetables.sampler_plan(st, RATE, "vocal", "v.wav")
    assert "semitone" not in v["oscillator"] and v["oscillator"]["sample_loop"] == "off"
    k = wavetables.sampler_plan(st, RATE, "bass", "b.wav", target_midi=43)
    ko = k["oscillator"]
    assert ko["octave"] * 12 + ko["semitone"] + ko["fine"] / 100 == pytest.approx(-2.0, abs=0.1)


def test_spec_parts_assemble_into_one_preset():
    parts = [serumspec.pluck(0.001, 0.2, 45.0), serumspec.chop(16), serumspec.room(20.0), serumspec.dirt("kDiode1", 40.0)]
    rev, dist = serumspec.fx_index_after(parts, "FXReverb"), serumspec.fx_index_after(parts, "FXDistortion")
    parts += [serumspec.duck(rev), serumspec.macros(0, 60.0, 1, 40.0, rev, 30.0, dist, 60.0)]
    osc = serumspec.table_osc("C:/sandbox/t.wav", 16)
    s = serumspec.assemble("CP - Test", "a test", [osc], [{"type": "lowpass_24", "cutoff": 0.4}], parts, serumspec.amp(0.001, 0.3, 0.0, 0.1))
    assert [e["decay"] for e in s["envelopes"]] == [0.3, 0.2] and len(s["lfos"]) == 2 and [m["name"] for m in s["macros"]] == ["GRIP", "SNAP", "ROOM", "DIRT"]
    dests = {(r["source"], r["destination"]) for r in s["mod_routes"]}
    assert {("env1", "filter0.cutoff"), ("lfo0", "oscillator0.volume"), ("lfo1", "fx0.wet"), ("macro2", "fx0.wet"), ("macro3", "fx1.wet")} <= dests
    gate = s["lfos"][0]["curve"]
    xs = [p["x"] for p in gate]
    assert xs[0] == 0.0 and xs[-1] == 1.0 and all(b > a for a, b in zip(xs, xs[1:])) and sum(1 for a, b in zip(gate, gate[1:]) if b["y"] > a["y"]) == 4
    assert s["lfos"][1]["curve"][0]["y"] == 1.0 and len(s["lfos"][1]["curve"]) == 3       # three points: a falling two-point curve renders blank
    with pytest.raises(ValueError):
        serumspec.chop(12)
