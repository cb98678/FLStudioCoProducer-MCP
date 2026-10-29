from __future__ import annotations

from coproducer import call
from coproducer.result import Result, ok

_FALL_BACK_ON = ("E_MODEL", "E_GPU_BUDGET", "E_NOT_FOUND", "E_UNSUPPORTED_API", "E_TIMEOUT")


def critique_audio(path: str, focus: str = "") -> Result:
    """Ask the audio-language model for a critique of an audio file. Without the model, fall back to the rule-based critique.

    The result has source 'model' or 'dsp'; meta.fallback is set when the model could not be used. Listen to model text with care.
    """
    prompt = "Critique this track's mix and arrangement. Be specific and list concrete problems first."
    if focus:
        prompt += " Focus on: " + focus
    got = call("run_model_op", model="flamingo", op="critique", args={"path": path, "prompt": prompt}, timeout_s=900)
    if got.ok:
        return ok({"text": got.value["text"], "source": "model"})
    if got.error.code not in _FALL_BACK_ON:
        return got
    dsp = call("critique_audio_dsp", path=path)
    return dsp if not dsp.ok else ok(dsp.value, fallback="critique_audio_dsp", model_error=got.error.code, model_error_detail=got.error.message[:600])
