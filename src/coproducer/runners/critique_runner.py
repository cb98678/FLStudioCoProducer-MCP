"""Music Flamingo audio critique (optional, non-commercial license). Runs inside the critique environment.

Docs checked 2026-10-19: https://huggingface.co/nvidia/music-flamingo-2601-hf and
https://huggingface.co/docs/transformers/main/en/model_doc/musicflamingo. 8B weights in BF16 (about 16 GB), card tests on A100/H100;
on a 24 GB card the brain must be unloaded first. If it does not fit, critique_audio falls back to DSP.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner_common import RunnerError, serve  # noqa: E402

STATE: dict = {}
MODEL_ID = "nvidia/music-flamingo-2601-hf"
MODEL_REVISION = "6b5be086d52f65a1e204cb0faf70bf54e2741ecd"  # the snapshot install-models downloads (stacks.STACKS["critique"]); a test keeps them equal
DEFAULT_PROMPT = ("Critique the mix of this track. Comment on low end, stereo width, clarity, balance between "
                  "drums, bass and lead, and anything that sounds wrong. Be specific.")


def build_conversation(path: str, prompt: str) -> list:
    return [{"role": "user", "content": [{"type": "text", "text": prompt or DEFAULT_PROMPT}, {"type": "audio", "path": path}]}]


def load(a: dict) -> dict:
    import torch
    from transformers import AutoProcessor, MusicFlamingoForConditionalGeneration
    model_id = a.get("variant") or MODEL_ID
    rev = a.get("revision") or (MODEL_REVISION if model_id == MODEL_ID else None)  # pinned, so a hub update cannot change the critic
    STATE["processor"] = AutoProcessor.from_pretrained(model_id, revision=rev)
    STATE["model"] = MusicFlamingoForConditionalGeneration.from_pretrained(model_id, revision=rev, dtype=torch.bfloat16, device_map="auto")
    return {"loaded": model_id, "revision": rev}


def critique(a: dict) -> dict:
    if "model" not in STATE:
        raise RunnerError("E_MODEL", "load the model first")
    proc, model = STATE["processor"], STATE["model"]
    inputs = proc.apply_chat_template(build_conversation(a["path"], a.get("prompt", "")), tokenize=True,
                                      add_generation_prompt=True, return_dict=True).to(model.device)
    inputs["input_features"] = inputs["input_features"].to(model.dtype)
    out = model.generate(**inputs, max_new_tokens=int(a.get("max_new_tokens", 512)))
    text = proc.batch_decode(out[:, inputs.input_ids.shape[1]:], skip_special_tokens=True)[0]
    return {"text": text.strip()}


if __name__ == "__main__":
    serve({"load": load, "unload": lambda a: STATE.clear() or True, "ping": lambda a: "pong", "critique": critique})
