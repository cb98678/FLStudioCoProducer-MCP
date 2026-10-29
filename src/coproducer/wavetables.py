"""Serum 2 wavetables and sampler sounds from a song's own material (skill serum-wavetables, 2026-10-28).

A wavetable frame is one cycle of 2048 samples (Serum's own table files: frames of 2048 samples, marked by a "clm " chunk, the format
serum-mcp writes, its preset/wavetable.py). A cycle cut straight from a stem is not one period long, so a table sliced from it buzzes
(serum-mcp's sample_source slices evenly and says so). Here every frame is read pitch-synchronously: the part's fundamental is tracked,
the complex level of every harmonic is fitted over a few whole periods (what repeats adds up, bleed that does not repeat averages out,
as in loopkit), and the cycle is rebuilt from those harmonics at exactly 2048 samples, band-limited, with its phases. Frames are phase
aligned (same fundamental phase) so they morph without cancelling, and the table is turned so its wrap point is the quietest place of the
cycle, where serum-mcp's 64-sample edge fade (applied to every frame it slices) costs least; edge_loss_db reports what is left.

Formula tables follow Serum's formula parser (x from -1 to 1 across the cycle, w = (x+1)/2, y the table position from 0 to 1, Serum 1
manual's wording; Serum 2 keeps the parser) and are evaluated here, because serum-mcp has no formula field.

The sampler plan reads a one-shot or a phrase for serum-mcp's sample_playback_source: Serum's sample oscillator plays a file at its
recorded pitch and speed on MIDI note 60 (FL's C5; serum-mcp confirmed it by ear), pitch and length coupled.
"""
from __future__ import annotations

import ast
import math
import struct
from pathlib import Path

import numpy as np

from coproducer import soundbrief

FRAME = 2048
TABLE_RATE = 44100
CLM = b"<!>2048 01000000 wavetable (www.xferrecords.com)"
SERUM_MCP_FADE = 64          # serum-mcp eada85a, wavetable.slice_sample_to_frames: min(64, 2048 // 8) samples faded in and out per frame
PEAK = 0.9                   # serum-mcp normalises every sliced frame to 0.9; doing the same here makes its slicing leave the frames as they are
SAMPLER_NOTE = 60            # the note the sample oscillator plays a file at its own pitch (serum-mcp docs/PARAMETER_SCHEMA.md, SampleOsc)
NOTE_NAMES = soundbrief.NOTE_NAMES


class TableError(ValueError):
    pass


def mono(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, float)
    return x.mean(axis=1) if x.ndim == 2 else x


def note_name(midi: float) -> str:
    n = int(round(midi))
    return "%s%d" % (NOTE_NAMES[n % 12], n // 12 - 1)


def f0_track(m: np.ndarray, rate: int, fmin: float = 30.0, fmax: float = 1500.0, hop_s: float = 0.01) -> tuple[np.ndarray, np.ndarray]:
    """(times, f0 in Hz or nan) by YIN (soundbrief.yin_f0) on windows of 2.2 periods of fmin, every hop_s."""
    n = int(2.2 * rate / fmin)
    times, f0 = [], []
    floor = 1e-3 * max(1e-9, float(np.max(np.abs(m))))
    for i in range(0, max(1, len(m) - n), int(hop_s * rate)):
        fr = m[i:i + n]
        f = soundbrief.yin_f0(fr, rate, fmin, fmax) if len(fr) == n and np.sqrt(np.mean(fr ** 2)) > floor else None
        times.append((i + n / 2) / rate)
        f0.append(f if f else np.nan)
    return np.array(times), np.array(f0)


def voiced_runs(times: np.ndarray, f0: np.ndarray, step_cents: float = 35.0, min_s: float = 0.05) -> list[dict]:
    """Stretches where the pitch holds (each frame within step_cents of the last), longest first: t0, t1, f0 (median), frames."""
    runs, cur = [], []
    for t, f in zip(times, f0):
        if np.isfinite(f) and cur and abs(1200 * math.log2(f / cur[-1][1])) <= step_cents:
            cur.append((t, f))
            continue
        if len(cur) > 1:
            runs.append(cur)
        cur = [(t, f)] if np.isfinite(f) else []
    if len(cur) > 1:
        runs.append(cur)
    out = [{"t0": r[0][0], "t1": r[-1][0], "f0": float(np.median([f for _t, f in r])), "frames": len(r)} for r in runs]
    return sorted([r for r in out if r["t1"] - r["t0"] >= min_s], key=lambda r: r["t0"] - r["t1"])


def harmonic_fit(m: np.ndarray, rate: int, t: float, f0: float, periods: int = 4) -> np.ndarray:
    """Complex level of every harmonic of f0 below the source's Nyquist (and below 1024, a 2048-sample cycle's limit) over `periods`
    whole periods from t, Hann weighted. Index 0 is the fundamental."""
    length = int(round(periods * rate / f0))
    i0 = int(round(t * rate))
    seg = m[i0:i0 + length]
    if len(seg) < length:
        raise TableError("the stretch ends before %d periods of %.1f Hz from %.3f s" % (periods, f0, t))
    w = np.hanning(length)
    k = np.arange(1, min(1023, int(0.5 * rate / f0 * 0.98)) + 1)
    ph = np.exp(-2j * np.pi * np.outer(k, np.arange(length)) * f0 / rate)
    return 2.0 * (ph @ (seg * w)) / w.sum()


def cycle_from(h: np.ndarray) -> np.ndarray:
    """One 2048-sample cycle from complex harmonic levels (index 0 the fundamental): band-limited, no DC."""
    spec = np.zeros(FRAME // 2 + 1, complex)
    spec[1:1 + len(h)] = h * FRAME / 2
    return np.fft.irfft(spec, FRAME)


def align(frames: list[np.ndarray]) -> tuple[list[np.ndarray], int]:
    """Give every frame the same fundamental phase, then turn the whole table by one shift so the wrap point is the quietest place
    (least level within the edge-fade length on either side of it, over all frames). Returns the frames and that shift."""
    out = []
    for f in frames:
        s = np.fft.rfft(f)
        s *= np.exp(-1j * np.angle(s[1]) * np.arange(len(s))) if abs(s[1]) > 1e-12 else 1.0
        out.append(np.fft.irfft(s, FRAME))
    stack = np.abs(np.array(out))
    width = SERUM_MCP_FADE
    best = min(range(0, FRAME, 16), key=lambda sh: float(np.sum(np.roll(stack, -sh, axis=1)[:, list(range(width)) + list(range(FRAME - width, FRAME))])))
    return [np.roll(f, -best) for f in out], best


def normalise(frames: list[np.ndarray], peak: float = PEAK) -> list[np.ndarray]:
    out = []
    for f in frames:
        f = f - f.mean()
        p = float(np.max(np.abs(f)))
        out.append(f * (peak / p) if p > 1e-9 else f)
    return out


def edge_loss_db(frames: list[np.ndarray], fade: int = SERUM_MCP_FADE) -> float:
    """How much serum-mcp's per-frame edge fade (sample_source) changes the table: error level against the table, in dB."""
    w = np.ones(FRAME)
    r = np.linspace(0.0, 1.0, fade)
    w[:fade] *= r
    w[-fade:] *= r[::-1]
    a = np.concatenate(frames)
    err = np.concatenate([f * (1 - w) for f in frames])
    return float(20 * np.log10(max(1e-12, np.sqrt(np.mean(err ** 2))) / max(1e-12, np.sqrt(np.mean(a ** 2)))))


def levels(frame: np.ndarray, count: int = 64) -> list[float]:
    """Harmonic amplitudes of a cycle, the loudest 1.0 (serum-mcp's custom_harmonics frame format)."""
    a = np.abs(np.fft.rfft(frame))[1:count + 1]
    return [round(float(v), 4) for v in a / max(1e-12, float(a.max()))]


def cycles(m: np.ndarray, rate: int, frames: int = 16, fmin: float = 30.0, fmax: float = 1500.0, periods: int = 4,
           f0: float = 0.0) -> dict:
    """A table read from the longest held note of m: `frames` pitch-synchronous cycles spread from its start to its end, so the table
    position moves from the note's attack side to its tail. f0 (Hz) skips the tracking and uses the whole stretch."""
    if f0:
        run = {"t0": 0.0, "t1": len(m) / rate - periods / f0, "f0": float(f0), "frames": 0}
    else:
        runs = voiced_runs(*f0_track(m, rate, fmin, fmax))
        if not runs:
            raise TableError("no held pitch found: a table needs a pitched note (use the sampler, or sample_source for a texture)")
        run = runs[0]
    p = periods / run["f0"]
    t_last = max(run["t0"], min(run["t1"], len(m) / rate - p) - 0.5 * p)
    times = np.linspace(run["t0"], t_last, frames) if frames > 1 else np.array([run["t0"]])
    fits = [harmonic_fit(m, rate, float(t), _local_f0(m, rate, float(t), run["f0"], periods), periods) for t in times]
    out, shift = align([cycle_from(h) for h in fits])
    out = normalise(out)
    midi = 69 + 12 * math.log2(run["f0"] / 440.0)
    return {"frames": out, "f0_hz": round(run["f0"], 2), "midi": round(midi, 2), "note": note_name(midi), "cents": round(100 * (midi - round(midi)), 1),
            "from_s": round(float(times[0]), 3), "to_s": round(float(times[-1] + p), 3), "periods": periods, "shift": shift,
            "edge_loss_db": round(edge_loss_db(out), 1), "first": levels(out[0], 16), "last": levels(out[-1], 16)}


def _local_f0(m: np.ndarray, rate: int, t: float, f0: float, periods: int) -> float:
    """The pitch right at t (YIN over the frame's own periods), kept within 50 cents of the note's: a slow drift or vibrato is followed."""
    seg = m[int(t * rate):int(t * rate) + int(2.2 * rate / (f0 * 0.8))]
    f = soundbrief.yin_f0(seg, rate, f0 * 0.8, f0 * 1.25) if len(seg) > 8 else None
    return f if f and abs(1200 * math.log2(f / f0)) <= 50 else f0


SAFE_FUNCS = {"sin": np.sin, "cos": np.cos, "tan": np.tan, "asin": np.arcsin, "acos": np.arccos, "atan": np.arctan, "sinh": np.sinh,
              "cosh": np.cosh, "tanh": np.tanh, "exp": np.exp, "log": np.log, "log10": np.log10, "sqrt": np.sqrt, "abs": np.abs,
              "sign": np.sign, "floor": np.floor, "ceil": np.ceil, "min": np.minimum, "max": np.maximum, "pow": np.power}
SAFE_NODES = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Call, ast.Name, ast.Constant, ast.Load, ast.Add, ast.Sub, ast.Mult, ast.Div,
              ast.Pow, ast.Mod, ast.USub, ast.UAdd)


def formula(expr: str, frames: int = 16) -> dict:
    """Evaluate a Serum formula (x, w, y, pi, e; the functions in SAFE_FUNCS; ^ is a power) into frames. Reports the jump at the wrap
    (z at x=+1 against x=-1: a sine-like table has none, a ramp has a saw's jump) and the first harmonics of the first and last frame."""
    tree = ast.parse(expr.strip().replace("^", "**"), mode="eval")
    for n in ast.walk(tree):
        if not isinstance(n, SAFE_NODES) or (isinstance(n, ast.Call) and not (isinstance(n.func, ast.Name) and n.func.id in SAFE_FUNCS)):
            raise TableError("not allowed in a formula: %s" % type(n).__name__)
        if isinstance(n, ast.Name) and n.id not in SAFE_FUNCS and n.id not in ("x", "w", "y", "pi", "e"):
            raise TableError("unknown name in the formula: %s" % n.id)
    code = compile(tree, "<formula>", "eval")
    x = -1.0 + 2.0 * np.arange(FRAME + 1) / FRAME
    raw = []
    with np.errstate(all="ignore"):
        for k in range(frames):
            env = {"x": x, "w": (x + 1) / 2, "y": k / (frames - 1) if frames > 1 else 0.0, "pi": math.pi, "e": math.e, **SAFE_FUNCS}
            z = np.broadcast_to(np.asarray(eval(code, {"__builtins__": {}}, env), float), x.shape)
            raw.append(np.nan_to_num(z, nan=0.0, posinf=1.0, neginf=-1.0))
    jump = max(float(abs(z[-1] - z[0])) for z in raw)
    out = normalise([z[:FRAME] for z in raw])
    return {"frames": out, "wrap_jump": round(jump, 3), "first": levels(out[0], 16), "last": levels(out[-1], 16),
            "edge_loss_db": round(edge_loss_db(out), 1)}


def turn_quiet(frames: list[np.ndarray]) -> list[np.ndarray]:
    """Turn a formula table so its wrap is at the quietest point (no phase alignment: a formula's frames already share their phase)."""
    stack = np.abs(np.array(frames))
    w = SERUM_MCP_FADE
    best = min(range(0, FRAME, 16), key=lambda sh: float(np.sum(np.roll(stack, -sh, axis=1)[:, list(range(w)) + list(range(FRAME - w, FRAME))])))
    return [np.roll(f, -best) for f in frames]


def write_table(path: str | Path, frames: list[np.ndarray]) -> Path:
    """A Serum wavetable WAV: mono 32-bit float at 44.1 kHz, frames of 2048 samples, with Serum's clm chunk."""
    if not frames or any(len(f) != FRAME for f in frames):
        raise TableError("every frame must be %d samples" % FRAME)
    data = np.concatenate(frames).astype("<f4").tobytes()
    fmt = struct.pack("<HHIIHH", 3, 1, TABLE_RATE, TABLE_RATE * 4, 4, 32)
    body = b"WAVE" + b"fmt " + struct.pack("<I", len(fmt)) + fmt + b"clm " + struct.pack("<I", len(CLM)) + CLM
    body += b"data" + struct.pack("<I", len(data)) + data
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"RIFF" + struct.pack("<I", len(body)) + body)
    return p


def read_table(path: str | Path) -> tuple[list[np.ndarray], bool]:
    """(frames, has the clm chunk) of a table written by write_table (mono 32-bit float)."""
    raw = Path(path).read_bytes()
    if raw[:4] != b"RIFF" or raw[8:12] != b"WAVE":
        raise TableError("%s is not a WAV file" % Path(path).name)
    pos, data, clm = 12, b"", False
    while pos + 8 <= len(raw):
        cid, size = raw[pos:pos + 4], struct.unpack_from("<I", raw, pos + 4)[0]
        clm = clm or (cid == b"clm " and raw[pos + 8:pos + 8 + size].startswith(b"<!>2048"))
        data = raw[pos + 8:pos + 8 + size] if cid == b"data" else data
        pos += 8 + size + (size & 1)
    x = np.frombuffer(data, "<f4").astype(float)
    if len(x) == 0 or len(x) % FRAME:
        raise TableError("%s does not hold whole 2048-sample frames" % Path(path).name)
    return list(x.reshape(-1, FRAME)), clm


def loop_points(m: np.ndarray, rate: int, f0: float, t0: float, t1: float, periods: int = 8) -> tuple[float, float] | None:
    """Percent loop start and end for a sustain loop: whole periods inside [t0, t1], each end on a rising zero crossing."""
    def rising(i: int) -> int:
        seg = m[i:i + int(rate / f0) + 2]
        z = np.where((seg[:-1] <= 0) & (seg[1:] > 0))[0]
        return i + int(z[0]) if len(z) else i
    span = int(round(periods * rate / f0))
    mid = int(0.5 * (t0 + t1) * rate)
    a = rising(max(int(t0 * rate), mid - span // 2))
    b = rising(a + span - 1)
    if b >= int(t1 * rate) or b <= a:
        return None
    return round(100.0 * a / len(m), 3), round(100.0 * b / len(m), 3)


ROLE_LOOP = {"vocal": "off", "drum": "off", "bass": "forward", "melodic": "forward", "texture": "forward"}


def sampler_plan(x: np.ndarray, rate: int, role: str, path: str = "", target_midi: float | None = None) -> dict:
    """What a file needs to play right on Serum's sample oscillator (serum-mcp sample_playback_source): its level, its left-right balance,
    its pitch, the transposition so a note plays as itself (or lands on target_midi when played on note 60), and the loop. A vocal plays
    at its own pitch on note 60 with no transposition (the person's rule: whole phrases at their own pitch); a drum too, unless
    target_midi tunes it (a kick to the key)."""
    x2 = np.asarray(x, float) if np.ndim(x) == 2 else np.asarray(x, float)[:, None]
    m = x2.mean(axis=1)
    rms = [float(np.sqrt(np.mean(x2[:, c] ** 2))) for c in range(x2.shape[1])]
    peak = float(np.max(np.abs(x2)))
    plan = {"seconds": round(len(m) / rate, 3), "rate": rate, "channels": x2.shape[1], "peak_dbfs": round(20 * math.log10(max(peak, 1e-9)), 1),
            "rms_dbfs": round(20 * math.log10(max(float(np.sqrt(np.mean(m ** 2))), 1e-9)), 1),
            "lr_balance_db": round(20 * math.log10(max(rms[0], 1e-9) / max(rms[-1], 1e-9)), 2), "role": role, "play_note": SAMPLER_NOTE}
    runs = voiced_runs(*f0_track(m, rate, 30.0, 1500.0))
    voiced = sum(r["t1"] - r["t0"] for r in runs) / max(plan["seconds"], 1e-9)
    osc = {"sample_playback_source": path, "sample_loop": ROLE_LOOP.get(role, "off"), "sample_center_pan": True}
    if runs and voiced > 0.2:
        p = 69 + 12 * math.log2(runs[0]["f0"] / 440.0)
        plan.update({"pitch_midi": round(p, 2), "pitch_note": note_name(p), "voiced_share": round(voiced, 2)})
        if role in ("bass", "melodic", "texture") or (role == "drum" and target_midi is not None):
            want = SAMPLER_NOTE if target_midi is None else float(target_midi)
            shift = want - p
            octv = int(round(shift / 12.0))
            semi = int(round(shift - 12 * octv))
            osc.update({"octave": float(octv), "semitone": float(semi), "fine": round(100 * (shift - 12 * octv - semi), 1)})
            plan["plays_as"] = "note n sounds as note n" if target_midi is None else "note 60 sounds as %s" % note_name(want)
        if osc["sample_loop"] != "off":
            lp = loop_points(m, rate, runs[0]["f0"], runs[0]["t0"], runs[0]["t1"])
            if lp:
                osc.update({"sample_loop_start": lp[0], "sample_loop_end": lp[1], "sample_loop_crossfade": 2.0})
            else:
                osc["sample_loop"] = "off"
    plan["oscillator"] = osc
    plan["warnings"] = [w for w in (
        "clips: peak at or above 0 dBFS" if peak >= 0.999 else "",
        "left and right differ by %.1f dB: sample_center_pan (on) balances them" % abs(plan["lr_balance_db"]) if abs(plan["lr_balance_db"]) > 1.5 else "",
        "pitch and length are coupled: notes away from 60 play faster or slower" if role in ("vocal", "drum") else "",
        "no clear pitch: played as it is on note 60" if "pitch_midi" not in plan and role in ("bass", "melodic") else "") if w]
    return plan
