"""Print Whisper word timestamps for short audio files, for checking where words really sit.

    python tools/word_times.py FILE.wav [FILE2.wav ...] [--model openai/whisper-large-v3]

Run with the interpreter that has torch and transformers. Times are seconds from the start of each file. Whisper's word times drift on sung vocals, so treat them as hints:
cut points come from the energy envelope (coproducer.vocalchops.islands), not from these numbers.
"""
from __future__ import annotations

import argparse

WHISPER_REVISION = "06f233fe06e710322aca913c1bc4249a0d71fce1"  # openai/whisper-large-v3 snapshot in use since 2026-10-22 (cached on the host)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--model", default="openai/whisper-large-v3")
    ap.add_argument("--revision", default=WHISPER_REVISION, help="the model snapshot; pinned so a hub update cannot change the transcripts")
    a = ap.parse_args()
    import numpy as np
    import soundfile as sf
    import torch
    from scipy.signal import resample_poly
    from transformers import pipeline

    dev = 0 if torch.cuda.is_available() else -1
    asr = pipeline("automatic-speech-recognition", model=a.model, revision=a.revision, device=dev, dtype=torch.float16 if dev == 0 else torch.float32)
    for p in a.files:
        x, sr = sf.read(p)
        x = x.mean(1) if x.ndim > 1 else x
        x = resample_poly(x, 16000, sr) if sr != 16000 else x
        x = np.concatenate([np.zeros(8000), x, np.zeros(8000)]).astype("float32")
        r = asr({"raw": x, "sampling_rate": 16000}, return_timestamps="word", generate_kwargs={"language": "en", "task": "transcribe"})
        words = " ".join("%s[%.2f-%.2f]" % (c["text"].strip(), (c["timestamp"][0] or 0) - 0.5, (c["timestamp"][1] or 0) - 0.5) for c in r["chunks"])
        print("%-22s %r  %s" % (p.replace("\\", "/").split("/")[-1], r["text"].strip(), words), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
