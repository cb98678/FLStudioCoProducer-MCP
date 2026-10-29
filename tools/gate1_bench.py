"""Gate 1 acceptance bench: G1-1 (measure report vs independent references) and G1-5 (BPM and key accuracy).

    python tools/gate1_bench.py --out docs/reports/gate1.json [--only g1_1|g1_5] [--seconds-per-key 6]

References, none of them our own code:
  * maths     peak, RMS, correlation, clipping computed directly from the samples or known from how the signal was built
  * ffmpeg    EBU R128 loudness, loudness range and true peak (the `ebur128` filter), when ffmpeg is on PATH
  * pyloudnorm  integrated loudness
  * librosa   tempo and key-profile cross-check for G1-5 (comparison only, never the pass rule)
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from coproducer import dsp, synth  # noqa: E402
from coproducer.registry import Registry  # noqa: E402

RATE = synth.RATE

# Pass rules for G1-5, accepted by the owner on 2026-10-22 (docs/GATE1.md). The labeled set is synthetic until real
# tracks with known tempo and key are supplied; the rules say what the estimators must do on it.
THRESHOLDS = {"tempo_truth_in_candidates": 0.99, "tempo_silent_wrong": 0, "tempo_genre_guided_exact": 0.95, "tempo_blind_exact": 0.70,
              "key_exact": 0.90, "key_exact_or_relative": 0.95}


def g1_5_verdict(r: dict) -> dict:
    t, k, th = r["tempo"], r["key"], THRESHOLDS
    checks = {"tempo_truth_in_candidates": t["truth_in_candidates_rate"] >= th["tempo_truth_in_candidates"],
              "tempo_silent_wrong": t["silent_wrong"] <= th["tempo_silent_wrong"],
              "tempo_genre_guided_exact": t["genre_guided_exact_rate"] >= th["tempo_genre_guided_exact"],
              "tempo_blind_exact": t["exact_rate"] >= th["tempo_blind_exact"],
              "key_exact": k["exact_rate"] >= th["key_exact"], "key_exact_or_relative": k["exact_or_relative_rate"] >= th["key_exact_or_relative"]}
    return {"thresholds": th, "checks": checks, "pass": all(checks.values())}


# ----------------------------------------------------------------------------- reference meters
def ffmpeg_ebur128(path: str) -> dict | None:
    if not shutil.which("ffmpeg"):
        return None
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True, timeout=120)
    tail = p.stderr.split("Summary:")[-1]

    def grab(label):
        m = re.search(rf"{label}:\s+(-?[\d.]+|-inf)", tail)
        return None if not m or m.group(1) == "-inf" else float(m.group(1))
    return {"lufs": grab("I"), "lra": grab("LRA"), "tp": grab("Peak")}


def pyln_lufs(x: np.ndarray, rate: int) -> float:
    import pyloudnorm as pyln
    return float(pyln.Meter(rate).integrated_loudness(x if x.ndim > 1 else x[:, None]))


# ----------------------------------------------------------------------------- G1-1 fixtures
def _stereo(x):
    return np.repeat(x[:, None], 2, axis=1) if x.ndim == 1 else x


def fixtures() -> list[dict]:
    """Each fixture: name, samples (n, ch), rate, subtype, and exact expectations where the maths gives them."""
    out = []
    s = lambda f, sec, amp, rate=RATE: synth.sine(f, sec, amp, rate).reshape(-1)  # noqa: E731
    out.append({"name": "sine_1k_-6dB", "x": _stereo(s(1000, 6, 0.5)), "exact": {"peak": -6.02, "rms": -9.03, "corr": 1.0}})
    out.append({"name": "sine_1k_-20dB", "x": _stereo(s(1000, 6, 0.1)), "exact": {"peak": -20.0, "rms": -23.01, "corr": 1.0}})
    out.append({"name": "sine_100_-12dB", "x": _stereo(s(100, 6, 0.25)), "exact": {"peak": -12.04, "rms": -15.05, "corr": 1.0}})
    out.append({"name": "sine_1k_-60dB", "x": _stereo(s(1000, 6, 0.001)), "exact": {"peak": -60.0, "rms": -63.01, "corr": 1.0}})
    out.append({"name": "white_noise", "x": synth.noise(8, 0.2, RATE, 2, seed=3), "exact": {"corr_max": 0.1}})
    out.append({"name": "drum_loop_140", "x": synth.drum_loop(140, bars=8), "exact": {"corr": 1.0}})
    out.append({"name": "drum_loop_mono", "x": synth.drum_loop(128, bars=8, channels=1), "exact": {}})
    left = s(1000, 6, 0.4)
    out.append({"name": "out_of_phase", "x": np.stack([left, -left], axis=1), "exact": {"corr": -1.0}})
    out.append({"name": "side_only", "x": np.stack([left, -left], axis=1), "exact": {"corr": -1.0}})
    hard = np.clip(_stereo(s(440, 6, 1.6)), -1, 1)
    out.append({"name": "hard_clipped", "x": hard, "exact": {"peak": 0.0, "clipped_min": 1000}})
    # intersample over: an fs/4 sine at 45 degrees stores +-0.707*A in its samples while the waveform reaches A.
    # A = 1.2 puts the samples under full scale (-1.43 dBFS) and the true peak over it (+1.58 dBTP).
    # A slow fade in and out keeps the start and end from ringing, so every meter sees the same peak.
    n = np.arange(RATE * 6)
    fade = np.minimum(1.0, np.minimum(n, n[::-1]) / (0.5 * RATE))
    isp = 1.2 * fade * np.sin(2 * np.pi * 0.25 * n + math.pi / 4)
    out.append({"name": "intersample_over", "x": _stereo(isp), "exact": {"peak": 20 * math.log10(1.2 * math.sqrt(0.5)), "tp": 20 * math.log10(1.2)}})
    gap = np.concatenate([s(500, 3, 0.3), np.zeros(RATE * 2), s(500, 3, 0.3)])
    out.append({"name": "silence_gap", "x": _stereo(gap), "exact": {"silent_regions": 1}})
    stepped = np.concatenate([s(1000, 5, 0.02), s(1000, 5, 0.2), s(1000, 5, 0.02)])
    out.append({"name": "loudness_steps", "x": _stereo(stepped), "exact": {"lra_min": 10.0}})
    out.append({"name": "dc_offset", "x": _stereo(s(1000, 6, 0.3) + 0.2), "exact": {}})
    out.append({"name": "rate_44k_sine", "x": _stereo(s(1000, 6, 0.5, 44100)), "rate": 44100, "exact": {"peak": -6.02, "rms": -9.03}})
    out.append({"name": "rate_96k_sine", "x": _stereo(s(1000, 6, 0.5, 96000)), "rate": 96000, "exact": {"peak": -6.02, "rms": -9.03}})
    out.append({"name": "pcm16_sine", "x": _stereo(s(1000, 6, 0.5)), "subtype": "PCM_16", "exact": {"peak": -6.02, "rms": -9.03}})
    out.append({"name": "pcm24_sine", "x": _stereo(s(1000, 6, 0.5)), "subtype": "PCM_24", "exact": {"peak": -6.02, "rms": -9.03}})
    out.append({"name": "bass_in_side", "x": np.stack([s(60, 6, 0.3), -s(60, 6, 0.3)], axis=1), "exact": {"low_end_mono": False}})
    return out


def close(a, b, tol):
    return a is not None and b is not None and abs(a - b) <= tol


def g1_1(workdir: Path) -> dict:
    reg = Registry(ROOT / "modules", ceiling="A2").load()
    reg.activate()
    rows, fails = [], 0
    tol = {"peak": 0.1, "rms": 0.1, "lufs": 0.15, "lra": 0.6, "tp": 0.35, "corr": 0.02}
    for fx in fixtures():
        rate = fx.get("rate", RATE)
        path = synth.to_wav(str(workdir / f"{fx['name']}.wav"), fx["x"], rate, fx.get("subtype", "FLOAT"))
        r = reg.call("build_measure_report", path=path)
        row = {"fixture": fx["name"], "checks": []}
        if not r.ok:
            row["checks"].append(("report", "FAIL", r.error.code))
            fails += 1
            rows.append(row)
            continue
        v, ex = r.value, fx["exact"]

        def chk(what, got, want, t, kind="maths", row=row):
            nonlocal fails
            good = close(got, want, t)
            fails += 0 if good else 1
            row["checks"].append({"what": what, "got": got, "want": None if want is None else round(want, 3), "tol": t, "ref": kind, "ok": good})
        # data read back from the file, so a 16 bit file is compared with what 16 bit holds
        import soundfile as sf
        data, rr = sf.read(path, always_2d=True)
        if "peak" in ex:
            chk("sample_peak_db", v["sample_peak"]["peak_db"], ex["peak"], tol["peak"] + (0.02 if fx.get("subtype") == "PCM_16" else 0))
        if "rms" in ex:
            chk("rms_db", v["rms"]["rms_db"], ex["rms"], tol["rms"])
        if "corr" in ex and "correlation" in v:
            chk("correlation", v["correlation"]["correlation"], ex["corr"], tol["corr"])
        if "corr_max" in ex:
            row["checks"].append({"what": "correlation near 0", "got": v["correlation"]["correlation"], "want": f"|c| < {ex['corr_max']}",
                                  "ok": abs(v["correlation"]["correlation"]) < ex["corr_max"], "ref": "maths"})
            fails += 0 if row["checks"][-1]["ok"] else 1
        if "tp" in ex:
            chk("true_peak_dbtp", v["true_peak"]["true_peak_dbtp"], ex["tp"], tol["tp"])
            row["checks"].append({"what": "intersample_over flagged", "got": v["true_peak"]["intersample_over"], "want": True,
                                  "ok": v["true_peak"]["intersample_over"] is True, "ref": "maths"})
            fails += 0 if row["checks"][-1]["ok"] else 1
        if "clipped_min" in ex:
            ok_ = v["clipping"]["clipped_samples"] >= ex["clipped_min"]
            row["checks"].append({"what": "clipped_samples", "got": v["clipping"]["clipped_samples"], "want": f">= {ex['clipped_min']}", "ok": ok_, "ref": "maths"})
            fails += 0 if ok_ else 1
        if "silent_regions" in ex:
            n = len(v["silence"]["regions"])
            row["checks"].append({"what": "silent regions", "got": n, "want": ex["silent_regions"], "ok": n == ex["silent_regions"], "ref": "maths"})
            fails += 0 if n == ex["silent_regions"] else 1
        if "lra_min" in ex:
            ok_ = v.get("range", {}).get("lra_lu", 0) >= ex["lra_min"]
            row["checks"].append({"what": "loudness range", "got": v.get("range", {}).get("lra_lu"), "want": f">= {ex['lra_min']}", "ok": ok_, "ref": "maths"})
            fails += 0 if ok_ else 1
        if "low_end_mono" in ex:
            ok_ = v["low_end_mono"]["mono_below_cutoff"] is ex["low_end_mono"]
            row["checks"].append({"what": "low end mono flag", "got": v["low_end_mono"]["mono_below_cutoff"], "want": ex["low_end_mono"], "ok": ok_, "ref": "maths"})
            fails += 0 if ok_ else 1
        # independent loudness meters
        silent = float(np.max(np.abs(data))) < 1e-6
        if not silent:
            ff = ffmpeg_ebur128(path)
            if ff:
                chk("lufs vs ffmpeg", v["loudness"]["lufs"], ff["lufs"], tol["lufs"], "ffmpeg ebur128")
                if "range" in v and ff["lra"] is not None:
                    chk("lra vs ffmpeg", v["range"]["lra_lu"], ff["lra"], tol["lra"], "ffmpeg ebur128")
                if ff["tp"] is not None:
                    chk("true peak vs ffmpeg", v["true_peak"]["true_peak_dbtp"], ff["tp"], tol["tp"], "ffmpeg ebur128")
            chk("lufs vs pyloudnorm", v["loudness"]["lufs"], pyln_lufs(data, rr), tol["lufs"], "pyloudnorm")
        rows.append(row)
    n_checks = sum(len(r["checks"]) for r in rows)
    return {"fixtures": len(rows), "checks": n_checks, "failed": fails, "rows": rows, "tolerances": tol,
            "ffmpeg": bool(shutil.which("ffmpeg"))}


# ----------------------------------------------------------------------------- G1-5 BPM and key
def bpm_signal(bpm: float, seconds: float, swing: float = 0.0, noise_db: float | None = None, seed: int = 0, rate: int = RATE) -> np.ndarray:
    """Kick on every beat, hats on offbeats (optionally swung), a bass note per beat, optional noise bed."""
    rng = np.random.default_rng(seed)
    x = np.zeros(int(seconds * rate) + rate)
    beat = 60.0 / bpm
    k, h = synth.kick(rate).reshape(-1), synth.hat(rate).reshape(-1)
    i = 0
    while i * beat < seconds:
        t = i * beat
        s0 = int(t * rate)
        x[s0:s0 + len(k)] += k[: len(x) - s0]
        off = t + beat / 2 * (1 + swing)
        s1 = int(off * rate)
        if off < seconds:
            x[s1:s1 + len(h)] += h[: len(x) - s1]
        i += 1
    x = x[: int(seconds * rate)]
    if noise_db is not None:
        x = x + rng.normal(0, 10 ** (noise_db / 20), len(x))
    return (x / max(np.max(np.abs(x)), 1e-9) * 0.8)[:, None]



def pattern_signal(kind: str, bpm: float, bars: int = 12, rate: int = RATE, seed: int = 0) -> np.ndarray:
    """Genre-shaped drum patterns. Positions are in beats within a 4 beat bar. The 'truth' is the producer's tempo
    (dubstep at 140 feels half time, but 140 is the number on the project)."""
    rng = np.random.default_rng(seed)
    k, h = synth.kick(rate).reshape(-1), synth.hat(rate).reshape(-1)
    sn = rng.normal(0, 1, int(0.18 * rate)) * np.exp(-np.arange(int(0.18 * rate)) / (0.04 * rate)) * 0.7
    pat = {
        "techno": {"k": [0, 1, 2, 3], "s": [1, 3], "h": [0.5, 1.5, 2.5, 3.5]},
        "dubstep": {"k": [0], "s": [2], "h": [0.5 * i for i in range(8)]},
        "dnb": {"k": [0, 2.5], "s": [1, 3], "h": [0.5 * i for i in range(8)]},
        "house": {"k": [0, 1, 2, 3], "s": [1, 3], "h": [0.5, 1.5, 2.5, 3.5]},
        "hiphop": {"k": [0, 1.5, 2.5], "s": [1, 3], "h": [0.5 * i for i in range(8)]},
    }[kind]
    beat = 60.0 / bpm
    total = int(bars * 4 * beat * rate) + rate
    x = np.zeros(total)

    def put(sample, t):
        i = int(t * rate)
        if 0 <= i < total:
            x[i:i + len(sample)] += sample[: total - i]
    for b in range(bars):
        for key, sample in (("k", k), ("s", sn), ("h", h)):
            for pos in pat[key]:
                put(sample, (b * 4 + pos) * beat)
    x = x[: int(bars * 4 * beat * rate)]
    return (x / max(np.max(np.abs(x)), 1e-9) * 0.8)[:, None]


def key_signal(tonic: int, minor: bool, seconds: float, seed: int = 0, rate: int = RATE, cents: float = 0.0) -> np.ndarray:
    """A i-iv-v-i style progression (I-IV-V-I for major) of triads with a bass root and a melody, in the given key."""
    rng = np.random.default_rng(seed)
    scale = [0, 2, 3, 5, 7, 8, 10] if minor else [0, 2, 4, 5, 7, 9, 11]
    prog = [0, 3, 4, 0] if not minor else [0, 3, 4, 0]
    f = lambda semi, octave: 440.0 * 2 ** ((tonic + semi - 9 + 12 * (octave - 4) + cents / 100.0) / 12)  # noqa: E731
    per = seconds / len(prog)
    out = []
    for deg in prog:
        root = scale[deg]
        third = scale[(deg + 2) % 7] + (12 if (deg + 2) >= 7 else 0)
        fifth = scale[(deg + 4) % 7] + (12 if (deg + 4) >= 7 else 0)
        notes = [root, third, fifth]
        seg = sum(synth.sine(f(n, 3), per, 0.25, rate).reshape(-1) for n in notes)
        seg = seg + synth.sine(f(root, 2), per, 0.3, rate).reshape(-1)
        mel = np.concatenate([synth.sine(f(scale[int(rng.integers(0, 7))], 5), per / 4, 0.12, rate).reshape(-1) for _ in range(4)])
        m = min(len(seg), len(mel))
        out.append(seg[:m] + mel[:m])
    x = np.concatenate(out)
    return (x / max(np.max(np.abs(x)), 1e-9) * 0.8)[:, None]


def bpm_error_class(est: float, truth: float) -> str:
    """exact (within 1 percent), double/half (the usual octave confusion), or wrong."""
    if abs(est - truth) / truth <= 0.01:
        return "exact"
    for f, label in ((2.0, "double"), (0.5, "half")):
        if abs(est - truth * f) / (truth * f) <= 0.01:
            return label
    return "wrong"



def _tempo_row(x: np.ndarray, truth: float, rate: int) -> dict:
    cands = dsp.estimate_tempo(x, rate)
    top = cands[0]["bpm"] if cands else None
    ambiguous = dsp.tempo_ambiguity(cands)["ambiguous"]  # the same rule estimate_bpm_dsp applies
    return {"top": top, "class": bpm_error_class(top, truth) if top else "none", "ambiguous": ambiguous,
            "in_candidates": any(bpm_error_class(c["bpm"], truth) == "exact" for c in cands), "candidates": [c["bpm"] for c in cands],
            "strengths": [c["strength"] for c in cands]}


def g1_5(seconds_per_key: float) -> dict:
    rate = RATE
    tempo_rows = []
    bpms = [70, 85, 90, 100, 110, 120, 125, 128, 130, 135, 140, 150, 160, 170, 174, 180]
    cases = [("plain", dict(swing=0.0, noise_db=None)), ("swing", dict(swing=0.3, noise_db=None)), ("noisy", dict(swing=0.0, noise_db=-24))]
    for bpm in bpms:
        for label, kw in cases:
            x = bpm_signal(bpm, 24.0, seed=bpm, **kw)
            tempo_rows.append({"bpm": bpm, "case": label, **_tempo_row(x, bpm, rate)})
    ranges = {"techno": (120, 140), "house": (118, 130), "dubstep": (136, 152), "dnb": (165, 180), "hiphop": (70, 100)}
    for kind, lst in (("techno", [124, 128, 130, 132, 135]), ("house", [120, 124, 126, 128]), ("dubstep", [138, 140, 142, 150]),
                      ("dnb", [170, 172, 174, 176]), ("hiphop", [80, 90, 95])):
        for bpm in lst:
            x = pattern_signal(kind, bpm, 14 if bpm < 100 else 12, seed=bpm)
            lo, hi = ranges[kind]
            guided = dsp.estimate_tempo(x, rate, lo * 0.95, hi * 1.05)
            tempo_rows.append({"bpm": bpm, "case": kind, "guided_top": guided[0]["bpm"] if guided else None,
                               "guided_class": bpm_error_class(guided[0]["bpm"], bpm) if guided else "none", **_tempo_row(x, bpm, rate)})
    n = len(tempo_rows)
    exact = sum(r["class"] == "exact" for r in tempo_rows)
    octave = sum(r["class"] in ("double", "half") for r in tempo_rows)
    incand = sum(r["in_candidates"] for r in tempo_rows)
    silent_wrong = [r for r in tempo_rows if r["class"] != "exact" and not r["ambiguous"]]
    guided = [r for r in tempo_rows if "guided_class" in r]
    key_rows = []
    names = dsp.NOTE_NAMES
    conditions = ("clean", "detuned", "noisy", "with_drums")
    for tonic in range(12):
        for minor in (False, True):
            for cond in conditions:
                seed = tonic * 2 + int(minor)
                x = key_signal(tonic, minor, seconds_per_key * 4, seed=seed, rate=rate, cents=30.0 if cond == "detuned" else 0.0)
                if cond == "noisy":
                    x = x + np.random.default_rng(seed).normal(0, 10 ** (-14 / 20) * float(np.std(x)), x.shape)
                if cond == "with_drums":
                    d = pattern_signal("techno", 128, int(seconds_per_key * 4 * 128 / 240) + 1, rate=rate, seed=seed)[: len(x)]
                    x = x[: len(d)] * 0.7 + d * 0.5
                r = dsp.estimate_key(x, rate)
                truth = f"{names[tonic]} {'minor' if minor else 'major'}"
                rel = f"{names[(tonic + 3) % 12 if minor else (tonic + 9) % 12]} {'major' if minor else 'minor'}"
                cls = "exact" if r["key"] == truth else ("relative" if r["key"] == rel else "wrong")
                key_rows.append({"truth": truth, "condition": cond, "got": r["key"], "class": cls, "score": r["score"], "margin": r["margin"], "runner_up": r["runner_up"]})
    kn = len(key_rows)
    kexact = sum(r["class"] == "exact" for r in key_rows)
    krel = sum(r["class"] == "relative" for r in key_rows)
    out = {
        "tempo": {"cases": n, "exact": exact, "octave_error": octave, "wrong": n - exact - octave,
                  "exact_rate": round(exact / n, 3), "exact_or_octave_rate": round((exact + octave) / n, 3), "truth_in_candidates_rate": round(incand / n, 3),
                  "silent_wrong": len(silent_wrong), "silent_wrong_cases": [(r["case"], r["bpm"], r["top"]) for r in silent_wrong],
                  "flagged_when_correct": sum(r["ambiguous"] for r in tempo_rows if r["class"] == "exact"), "correct": exact,
                  "genre_guided_cases": len(guided), "genre_guided_exact_rate": round(sum(r["guided_class"] == "exact" for r in guided) / max(len(guided), 1), 3),
                  "rows": tempo_rows},
        "key": {"cases": kn, "exact": kexact, "relative_confusion": krel, "wrong": kn - kexact - krel,
                "exact_rate": round(kexact / kn, 3), "exact_or_relative_rate": round((kexact + krel) / kn, 3),
               "by_condition": {c: round(sum(r["class"] == "exact" for r in key_rows if r["condition"] == c) / sum(r["condition"] == c for r in key_rows), 3) for c in conditions},
               "rows": key_rows},
    }
    try:
        import librosa
        diffs = []
        for bpm in (90, 128, 140, 174):
            x = bpm_signal(bpm, 24.0, seed=bpm)
            t = float(np.atleast_1d(librosa.beat.beat_track(y=x[:, 0].astype(np.float32), sr=rate)[0])[0])
            diffs.append({"bpm": bpm, "librosa": round(t, 2), "class": bpm_error_class(t, bpm)})
        out["tempo"]["librosa_comparison"] = diffs
    except Exception as e:  # reference only
        out["tempo"]["librosa_comparison"] = f"unavailable: {type(e).__name__}"
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="gate1.json")
    ap.add_argument("--only", choices=["g1_1", "g1_5"])
    ap.add_argument("--seconds-per-key", type=float, default=6.0)
    a = ap.parse_args()
    out_path = Path(a.out)
    res = json.loads(out_path.read_text()) if a.only and out_path.exists() else {}
    with tempfile.TemporaryDirectory() as d:
        if a.only in (None, "g1_1"):
            res["g1_1"] = g1_1(Path(d))
            print(f"G1-1: {res['g1_1']['fixtures']} fixtures, {res['g1_1']['checks']} checks, {res['g1_1']['failed']} failed", flush=True)
        if a.only in (None, "g1_5"):
            res["g1_5"] = g1_5(a.seconds_per_key)
            res["g1_5"]["verdict"] = g1_5_verdict(res["g1_5"])
            t, k = res["g1_5"]["tempo"], res["g1_5"]["key"]
            print(f"G1-5 tempo: {t['cases']} cases, exact {t['exact_rate']:.1%}, exact or octave {t['exact_or_octave_rate']:.1%}, truth in candidates {t['truth_in_candidates_rate']:.1%}, silent wrong {t['silent_wrong']}, genre-guided exact {t['genre_guided_exact_rate']:.1%}", flush=True)
            print(f"G1-5 verdict: {'PASS' if res['g1_5']['verdict']['pass'] else 'FAIL'} {res['g1_5']['verdict']['checks']}", flush=True)
            print(f"G1-5 key: {k['cases']} cases, exact {k['exact_rate']:.1%}, exact or relative {k['exact_or_relative_rate']:.1%}", flush=True)
    out_path.write_text(json.dumps(res, indent=1, default=str))
    bad = res.get("g1_1", {}).get("failed") or (res.get("g1_5") and not res["g1_5"]["verdict"]["pass"])
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
