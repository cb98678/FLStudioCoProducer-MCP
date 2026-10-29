"""Transcribe a vocal stem with word timestamps using Whisper through transformers. Run on the machine with the GPU in the pinned critique environment
(models/envs/critique: torch 2.11.0, transformers 5.20.2, see models/locks/critique.txt), not a system Python.

    python tools/transcribe_vocals.py VOCALS.wav OUT.json [--model openai/whisper-large-v3] [--language en]

Writes {"text": "...", "words": [{"word", "start", "end"}], "model": "..."}. Lyrics over music are imperfect: show the text to the artist and correct it before anything is regenerated from it.
"""
from __future__ import annotations

import argparse
import json

WHISPER_REVISION = "06f233fe06e710322aca913c1bc4249a0d71fce1"  # openai/whisper-large-v3 snapshot in use since 2026-10-22 (cached on the host)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("wav")
    ap.add_argument("out")
    ap.add_argument("--model", default="openai/whisper-large-v3")
    ap.add_argument("--revision", default=WHISPER_REVISION, help="the model snapshot; pinned so a hub update cannot change the transcripts")
    ap.add_argument("--language", default="en")
    a = ap.parse_args()
    import soundfile as sf
    import torch
    from scipy.signal import resample_poly
    from transformers import pipeline

    x, sr = sf.read(a.wav)
    x = x.mean(1) if x.ndim > 1 else x
    if sr != 16000:
        x = resample_poly(x, 16000, sr)
    dev = 0 if torch.cuda.is_available() else -1
    asr = pipeline("automatic-speech-recognition", model=a.model, revision=a.revision, device=dev, dtype=torch.float16 if dev == 0 else torch.float32)
    r = asr({"raw": x.astype("float32"), "sampling_rate": 16000}, chunk_length_s=30, return_timestamps="word", generate_kwargs={"language": a.language, "task": "transcribe"})
    words = [{"word": c["text"].strip(), "start": c["timestamp"][0], "end": c["timestamp"][1]} for c in r["chunks"]]
    json.dump({"text": r["text"].strip(), "words": words, "model": a.model}, open(a.out, "w"), indent=1)
    print("words", len(words))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
