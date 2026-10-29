"""Transcribe each chop one-shot with Whisper to confirm it holds the words it is named for.

    python tools/check_chops.py AUDIODIR OUT.json [--model openai/whisper-large-v3]

Run with the interpreter that has torch and transformers. Prints one line per chop and writes {name: text}.
"""
from __future__ import annotations

import argparse
import glob
import json
import os


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("out")
    ap.add_argument("--model", default="openai/whisper-large-v3")
    a = ap.parse_args()
    import numpy as np
    import soundfile as sf
    import torch
    from scipy.signal import resample_poly
    from transformers import pipeline

    dev = 0 if torch.cuda.is_available() else -1
    asr = pipeline("automatic-speech-recognition", model=a.model, device=dev, torch_dtype=torch.float16 if dev == 0 else torch.float32)
    res = {}
    for p in sorted(glob.glob(os.path.join(a.audio, "CP_Chop_*.wav"))):
        x, sr = sf.read(p)
        x = x.mean(1) if x.ndim > 1 else x
        x = resample_poly(x, 16000, sr) if sr != 16000 else x
        x = np.concatenate([np.zeros(8000), x, np.zeros(8000)]).astype("float32")
        r = asr({"raw": x, "sampling_rate": 16000}, generate_kwargs={"language": "en", "task": "transcribe"})
        name = os.path.basename(p)[8:-4]
        res[name] = r["text"].strip()
        print("%-10s %.2fs  %r" % (name, len(x) / 16000 - 1, res[name]))
    json.dump(res, open(a.out, "w"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
