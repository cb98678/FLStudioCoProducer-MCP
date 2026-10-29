"""Clean vocal source files with the vocalfx chain. Length-preserving, so FL clip offsets stay valid. Run from the repo root.

    python tools/vocal_clean.py OUT_DIR FILE [FILE ...] [--region START,END [--keep-length]] [--nr 0.6] [--target DBFS] [--hpf 100]

For every FILE it writes OUT_DIR/<stem>_vc.wav (24-bit, same rate and channel count) and one OUT_DIR/vocal_clean_report.json
with before and after levels. --region START,END (seconds, applied to every FILE) cuts to that window first; use it for long
sources where the playlist only uses a part. The report records the region start, because the clip offsets inside the
project then have to move earlier by that amount (tools/vocal_patch.py does this). --keep-length avoids that: the output is
as long as the source, with the original audio outside the region. Use it for any sample whose channel is tempo-stretched,
because FL ties the stretch to the file length and a shorter file changes the clip speed.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from coproducer import vocalfx  # noqa: E402


def read_any(path: Path) -> tuple[np.ndarray, int]:
    """soundfile first; ffmpeg for mp3/opus/anything it cannot open. Returns (frames, channels) float64."""
    try:
        x, sr = sf.read(str(path), always_2d=True)
        return x, sr
    except Exception:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / "d.wav"
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(path), "-c:a", "pcm_f32le", str(tmp)], check=True)
            x, sr = sf.read(str(tmp), always_2d=True)
            return x, sr


def stats(x: np.ndarray, sr: int) -> dict:
    m = x.mean(axis=1)
    voiced = np.abs(m) > 10 ** (-40 / 20)
    rms = float(np.sqrt(np.mean(m[voiced] ** 2))) if voiced.any() else 0.0
    f = np.fft.rfftfreq(4096, 1 / sr)
    n = len(m) // 4096
    if n:
        spec = np.abs(np.fft.rfft(m[: n * 4096].reshape(n, 4096) * np.hanning(4096), axis=1)).mean(0)
    else:
        spec = np.zeros(len(f))
    band = lambda lo, hi: float(20 * np.log10(np.sqrt(np.mean(spec[(f >= lo) & (f < hi)] ** 2)) + 1e-12))
    return {"peak_db": round(float(vocalfx.db(np.max(np.abs(m)))), 1), "voiced_rms_db": round(float(vocalfx.db(rms)), 1),
            "low_100_300": round(band(100, 300), 1), "mid_1k_3k": round(band(1000, 3000), 1), "hi_5k_9k": round(band(5000, 9000), 1)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--region")
    ap.add_argument("--keep-length", action="store_true",
                    help="with --region: write a file as long as the source, original audio outside the region (FL ties stretch to file length)")
    ap.add_argument("--nr", type=float, default=0.6)
    ap.add_argument("--target", type=float, default=None, help="voiced RMS in dBFS; default keeps each file at the level it had")
    ap.add_argument("--hpf", type=float, default=100.0)
    a = ap.parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    report = {}
    for name in a.files:
        src = Path(name)
        x, sr = read_any(src)
        t0 = 0.0
        full = None
        if a.region:
            t0, t1 = (float(v) for v in a.region.split(","))
            if a.keep_length:
                full = x.copy()
            x = x[int(t0 * sr):int(t1 * sr)]
        mono = np.allclose(x[:, 0], x[:, -1], atol=1e-4) if x.shape[1] > 1 else True
        chans = [x[:, 0]] if mono else [x[:, c] for c in range(x.shape[1])]
        y = np.stack([vocalfx.clean_vocal(c, sr, hpf_hz=a.hpf, nr_amount=a.nr, target_rms_db=a.target) for c in chans], axis=1)
        if mono and x.shape[1] > 1:
            y = np.repeat(y, x.shape[1], axis=1)
        if full is not None:
            i0 = int(t0 * sr)
            fade = int(0.01 * sr)
            y = np.asarray(y, dtype=np.float64)
            ramp = np.linspace(0.0, 1.0, fade)[:, None]
            y[:fade] = y[:fade] * ramp + full[i0:i0 + fade] * (1 - ramp)
            y[-fade:] = y[-fade:] * ramp[::-1] + full[i0 + len(y) - fade:i0 + len(y)] * (1 - ramp[::-1])
            full[i0:i0 + len(y)] = y
            y, t0 = full, 0.0
        dst = out / (src.stem + "_vc.wav")
        sf.write(str(dst), y, sr, subtype="PCM_24")
        report[src.name] = {"out": dst.name, "rate": sr, "channels": int(x.shape[1]), "region_start_s": t0, "frames": int(len(y)),
                            "before": stats(x, sr), "after": stats(y, sr)}
        print(src.name, report[src.name]["before"], "->", report[src.name]["after"], flush=True)
    (out / "vocal_clean_report.json").write_text(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
