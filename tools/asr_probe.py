"""Transcribe many windows of one audio file with Whisper, to see which cut points give whole words.

    python tools/asr_probe.py FILE.wav "136.9:137.8" "136.9:138.1" ... [--model openai/whisper-large-v3]

Run with the pinned critique environment (models\\envs\\critique\\Scripts\\python.exe, see docs/DEPENDENCIES.md), which has torch, transformers and the cached Whisper snapshot. Each window is seconds start:end in FILE. Prints the transcript of each.
Whisper alone is not trusted for word times (see tools/word_times.py), but the transcript of a window that ends or starts on a word is a usable check
that a cut did not drop or add a syllable.
"""
from __future__ import annotations

import argparse
import json

WHISPER_REVISION = "06f233fe06e710322aca913c1bc4249a0d71fce1"  # openai/whisper-large-v3 snapshot in use since 2026-10-22 (cached on the host)


def load(model: str, revision: str = WHISPER_REVISION):
    import torch
    from transformers import pipeline

    dev = 0 if torch.cuda.is_available() else -1
    return pipeline("automatic-speech-recognition", model=model, revision=revision, device=dev, dtype=torch.float16 if dev == 0 else torch.float32)


def transcribe(asr, x, sr: int) -> str:
    import numpy as np
    from scipy.signal import resample_poly

    x = x.mean(1) if x.ndim > 1 else x
    x = resample_poly(x, 16000, sr) if sr != 16000 else x
    x = np.concatenate([np.zeros(8000), x, np.zeros(8000)]).astype("float32")
    r = asr({"raw": x, "sampling_rate": 16000}, generate_kwargs={"language": "en", "task": "transcribe", "num_beams": 1})
    return r["text"].strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("windows", nargs="+")
    ap.add_argument("--model", default="openai/whisper-large-v3")
    ap.add_argument("--revision", default=WHISPER_REVISION, help="the model snapshot; pinned so a hub update cannot change the transcripts")
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    import soundfile as sf

    x, sr = sf.read(a.file, dtype="float32", always_2d=True)
    asr = load(a.model, a.revision)
    out = []
    for w in a.windows:
        s, e = (float(v) for v in w.split(":"))
        t = transcribe(asr, x[int(s * sr) : int(e * sr)], sr)
        out.append({"start": s, "end": e, "text": t})
        print("%8.3f %8.3f  %s" % (s, e, t), flush=True)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
