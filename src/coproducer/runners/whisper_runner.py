"""Whisper word timestamps for a vocal stem, inside the critique environment (transformers), at the pinned snapshot.

Same call as tools/transcribe_vocals.py (verified on the host 2026-10-25); here it runs through the scheduler, so song intake gets the words in
one call. Whisper's word times drift on sung vocals: the remix pipeline uses them to find the lines and the chops, and cuts on the audio.
Source: https://huggingface.co/openai/whisper-large-v3 (Apache-2.0).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner_common import serve  # noqa: E402

STATE: dict = {}
MODEL_ID = "openai/whisper-large-v3"
MODEL_REVISION = "06f233fe06e710322aca913c1bc4249a0d71fce1"  # stacks.WHISPER_REVISION; a test keeps them equal


def load(a: dict) -> dict:
    import torch
    from transformers import pipeline
    dev = 0 if torch.cuda.is_available() else -1
    STATE["asr"] = pipeline("automatic-speech-recognition", model=MODEL_ID, revision=MODEL_REVISION, device=dev,
                            dtype=torch.float16 if dev == 0 else torch.float32)
    return {"loaded": MODEL_ID, "revision": MODEL_REVISION}


def words(a: dict) -> dict:
    import soundfile as sf
    from scipy.signal import resample_poly
    x, sr = sf.read(a["path"])
    x = x.mean(1) if x.ndim > 1 else x
    if sr != 16000:
        x = resample_poly(x, 16000, sr)
    gen = {"language": a.get("language", "en"), "task": "transcribe"}
    if a.get("windows"):  # short windows, each on its own (asrclean: a loop over a long stretch is redone phrase by phrase)
        out, texts = [], []
        for t0, t1 in a["windows"]:
            seg = x[int(max(0.0, t0) * 16000):int(t1 * 16000)].astype("float32")
            if len(seg) < 1600:
                continue
            r = STATE["asr"]({"raw": seg, "sampling_rate": 16000}, return_timestamps="word", generate_kwargs=gen)
            for c in r["chunks"]:
                s, e = c["timestamp"]
                out.append({"word": c["text"].strip(), "start": round(t0 + (s or 0.0), 3), "end": None if e is None else round(t0 + e, 3)})
            texts.append(r["text"].strip())
        return {"text": " ".join(texts), "words": out, "model": MODEL_ID, "revision": MODEL_REVISION}
    r = STATE["asr"]({"raw": x.astype("float32"), "sampling_rate": 16000}, chunk_length_s=30, return_timestamps="word", generate_kwargs=gen)
    out = [{"word": c["text"].strip(), "start": c["timestamp"][0], "end": c["timestamp"][1]} for c in r["chunks"]]
    return {"text": r["text"].strip(), "words": out, "model": MODEL_ID, "revision": MODEL_REVISION}


if __name__ == "__main__":
    serve({"load": load, "unload": lambda a: STATE.clear() or True, "ping": lambda a: "pong", "words": words})
