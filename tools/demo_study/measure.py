"""Measure the full-mix renders of the FL demo songs (sandbox copies): whole-song and per-section loudness, band balance, width,
crest, centroid and sidechain pump depth. Run on the host from C:\\coproducer:

    .venv\\Scripts\\python.exe tools\\demo_study\\measure.py

Reads sandbox\\demo_study\\wav\\*.wav and sandbox\\demo_study\\sections.json (tools/demo_study/sections.py), writes
sandbox\\demo_study\\measure\\<song>.json and all.json (copy all.json to docs/demo_study/measure_full.json).
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from coproducer import dsp  # noqa: E402

WAV = ROOT / "sandbox" / "demo_study" / "wav"
OUT = ROOT / "sandbox" / "demo_study" / "measure"
SECS = json.loads((ROOT / "sandbox" / "demo_study" / "sections.json").read_text(encoding="utf-8"))
BANDS = {"sub": (20, 60), "bass": (60, 150), "low_mid": (150, 500), "mid": (500, 2000), "high_mid": (2000, 5000), "presence": (5000, 10000), "air": (10000, 20000)}


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def match(stem: str) -> str | None:
    """The sections key for a render's file name: the longest shared prefix (the render names are cut at 60 characters, and two
    Electroconductor files share their first 24)."""
    n = norm(stem)

    def common(k: str) -> int:
        kk, i = norm(k), 0
        while i < min(len(kk), len(n)) and kk[i] == n[i]:
            i += 1
        return i
    best = max(SECS, key=common)
    return best if common(best) >= min(16, len(norm(best))) else None   # a short title (LeriQ SHINE) matches in full


def width_db(x: np.ndarray) -> float:
    m = (x[:, 0] + x[:, 1]) / 2
    s = (x[:, 0] - x[:, 1]) / 2
    em, es = float(np.mean(m * m)), float(np.mean(s * s))
    return round(10 * math.log10(max(es, 1e-12) / max(em, 1e-12)), 2)


def low_width_db(x: np.ndarray, rate: int) -> float:
    sos = signal.butter(4, 120, "low", fs=rate, output="sos")
    return width_db(signal.sosfilt(sos, x, axis=0))


def crest_db(x: np.ndarray) -> float:
    m = np.abs(x).max()
    r = math.sqrt(float(np.mean(x * x)))
    return round(20 * math.log10(max(m, 1e-9) / max(r, 1e-9)), 2)


def short_lufs(x: np.ndarray, rate: int) -> float:
    t, l = dsp.window_loudness(x, rate, 3.0, 1.0)
    l = l[l > -70]
    if not len(l):
        return -99.0
    return round(10 * math.log10(float(np.mean(10 ** (l / 10)))), 2)


def pump(x: np.ndarray, rate: int, bpm: float) -> dict:
    """Fold the 150 Hz to 2 kHz envelope (synths, bass harmonics; the kick's body is below) and the 40 to 100 Hz envelope (kick) on the beat.
    depth_db: the swing of the synth envelope over one beat; dip_at: where in the beat (0..1) it is lowest; kick_at: where the kick peaks."""
    m = dsp.mono(x)
    hop = int(rate * 0.005)
    out = {}
    for name, (lo, hi) in (("synth", (150, 2000)), ("kick", (40, 100))):
        sos = signal.butter(4, [lo, hi], "band", fs=rate, output="sos")
        y = signal.sosfilt(sos, m)
        env = np.sqrt(np.convolve(y * y, np.ones(hop * 2) / (hop * 2), mode="same")[::hop] + 1e-12)
        beat = 60.0 / bpm / 0.005
        nb = int(len(env) / beat)
        if nb < 8:
            return {}
        bins = 40
        acc = np.zeros(bins)
        cnt = np.zeros(bins)
        for i in range(len(env)):
            ph = (i % beat) / beat
            k = min(bins - 1, int(ph * bins))
            acc[k] += env[i]
            cnt[k] += 1
        curve = 20 * np.log10(acc / np.maximum(cnt, 1) + 1e-12)
        out[name] = curve
    s, k = out["synth"], out["kick"]
    return {"depth_db": round(float(s.max() - s.min()), 2), "dip_at": round(float(np.argmin(s)) / len(s), 3),
            "peak_at": round(float(np.argmax(s)) / len(s), 3), "kick_at": round(float(np.argmax(k)) / len(k), 3),
            "kick_swing_db": round(float(k.max() - k.min()), 2)}


def measure(path: Path, info: dict) -> dict:
    x, rate = sf.read(str(path), dtype="float32", always_2d=True)
    x = x.astype(np.float64)
    bpm = info["bpm"]
    bar_s = 240.0 / bpm
    t_lufs, lufs = dsp.window_loudness(x, rate, 3.0, 1.0)
    lra, lo, hi = dsp.loudness_range(lufs)
    r = {"file": path.name, "seconds": round(len(x) / rate, 1), "bpm": bpm, "lufs": round(dsp.integrated_loudness(x, rate), 2),
         "true_peak_db": round(dsp.db(dsp.true_peak(x[: rate * 240], rate)), 2), "lra": round(lra, 2), "crest_db": crest_db(x),
         "corr": round(dsp.correlation(x[:, 0], x[:, 1]), 3), "width_db": width_db(x), "low_width_db": low_width_db(x, rate),
         "bands": dsp.band_energy_db(x, rate, BANDS), "centroid_hz": round(dsp.spectral_centroid(x, rate), 1), "sections": []}
    loudest = None
    for s in info["sections"]:
        a = int((s["start_bar"] - 1) * bar_s * rate)
        b = int((s["start_bar"] - 1 + s["bars"]) * bar_s * rate)
        seg = x[a:min(b, len(x))]
        if len(seg) < rate * 2:
            continue
        row = {"name": s["name"], "start_bar": s["start_bar"], "bars": s["bars"], "lufs": short_lufs(seg, rate), "bands": dsp.band_energy_db(seg, rate, BANDS),
               "width_db": width_db(seg), "centroid_hz": round(dsp.spectral_centroid(seg, rate), 1), "crest_db": crest_db(seg)}
        r["sections"].append(row)
        if loudest is None or row["lufs"] > loudest[0]:
            loudest = (row["lufs"], a, b)
    if loudest:
        r["pump_loudest_section"] = pump(x[loudest[1]:loudest[2]], rate, bpm)
    return r


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    allr = {}
    for p in sorted(WAV.glob("*.wav")):
        k = match(p.stem)
        if not k:
            print("NO SECTIONS FOR", p.name)
            continue
        dst = OUT / (k + ".json")
        if dst.is_file() and dst.stat().st_mtime > p.stat().st_mtime:
            allr[k] = json.loads(dst.read_text(encoding="utf-8"))
            continue
        try:
            r = measure(p, SECS[k])
        except Exception as e:  # noqa: BLE001
            print("FAIL", p.name, e)
            continue
        dst.write_text(json.dumps(r, indent=1), encoding="utf-8")
        allr[k] = r
        print(k, r["lufs"], r["crest_db"], r["width_db"], r.get("pump_loudest_section"))
        sys.stdout.flush()
    (OUT / "all.json").write_text(json.dumps(allr, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
