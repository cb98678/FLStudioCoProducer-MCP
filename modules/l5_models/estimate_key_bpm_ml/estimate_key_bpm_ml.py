from __future__ import annotations

import re

from coproducer import call
from coproducer.result import Result, fail, ok

_PROMPT = "Listen and reply in exactly this form and nothing else: key=<note and major or minor>; bpm=<number>"


def estimate_key_bpm_ml(path: str) -> Result:
    """Ask the audio-language model for key and tempo, as a cross-check on the DSP estimates.

    Errors: E_MODEL when the reply cannot be parsed. Treat the answer as a second opinion, never as the only one.
    """
    got = call("run_model_op", model="flamingo", op="critique", args={"path": path, "prompt": _PROMPT, "max_new_tokens": 40}, timeout_s=600)
    if not got.ok:
        return got
    key = re.search(r"key\s*=\s*([A-Ga-g][#b]?\s*(?:major|minor))", got.value["text"], re.I)
    bpm = re.search(r"bpm\s*=\s*(\d+(?:\.\d+)?)", got.value["text"], re.I)
    if not key or not bpm:
        return fail("E_MODEL", "the model reply could not be parsed", reply=got.value["text"][:200])
    return ok({"key": key.group(1).strip().title(), "bpm": float(bpm.group(1)), "source": "model"})
