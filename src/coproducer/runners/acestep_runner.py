"""ACE-Step 1.5 music generation. Runs inside the acestep environment (Python 3.11 to 3.12, installed with uv sync).

Docs checked 2026-10-18: https://github.com/ace-step/ACE-Step-1.5 and docs/en/INFERENCE.md.
Entry points: acestep.handler.AceStepHandler.initialize_service, acestep.llm_inference.LLMHandler.initialize,
acestep.inference.generate_music(dit, llm, GenerationParams, GenerationConfig, save_dir). The argument names below come
from that page; the smoke test (generate 5 s) is the proof on this machine.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner_common import RunnerError, serve  # noqa: E402

STATE: dict = {}
DIT = {"turbo": "acestep-v15-turbo", "sft": "acestep-v15-sft", "base": "acestep-v15-base"}
LM = {"0.6B": "acestep-5Hz-lm-0.6B", "1.7B": "acestep-5Hz-lm-1.7B", "4B": "acestep-5Hz-lm-4B"}
DEFAULT_STEPS = {"turbo": 8, "sft": 50, "base": 50}


def parse_variant(variant: str) -> tuple[str, str | None, str]:
    """'turbo+lm0.6B' gives ('acestep-v15-turbo', 'acestep-5Hz-lm-0.6B', 'turbo'); 'turbo' alone means no language model."""
    dit_key, _, lm_key = (variant or "turbo").partition("+lm")
    if dit_key not in DIT or (lm_key and lm_key not in LM):
        raise RunnerError("E_ARG", "unknown ACE-Step variant %r" % variant, known=sorted(DIT))
    return DIT[dit_key], (LM[lm_key] if lm_key else None), dit_key


def build_params(a: dict, dit_key: str, has_lm: bool) -> dict:
    """GenerationParams fields for one request. Turbo needs shift 3.0 set by hand, per the docs."""
    p = {"caption": a.get("prompt", ""), "lyrics": a.get("lyrics", ""), "instrumental": a.get("instrumental", True),
         "duration": float(a.get("duration", 30.0)), "inference_steps": a.get("steps", DEFAULT_STEPS[dit_key]),
         "seed": a.get("seed", -1), "task_type": a.get("task_type", "text2music"), "thinking": has_lm and a.get("task_type", "text2music") == "text2music"}
    for key, field in (("bpm", "bpm"), ("key", "keyscale"), ("time_signature", "timesignature")):
        if a.get(key):
            p[field] = a[key]
    if dit_key == "turbo":
        p["shift"] = 3.0
    if a.get("src_audio"):
        p["src_audio"] = a["src_audio"]
    if a.get("task_type") == "cover":
        p["audio_cover_strength"] = float(a.get("strength", 0.7))
    if a.get("task_type") == "repaint":
        p["repainting_start"], p["repainting_end"] = float(a["start_s"]), float(a["end_s"])
    return p


def load(a: dict) -> dict:
    from acestep.handler import AceStepHandler
    from acestep.llm_inference import LLMHandler
    root = a.get("root") or os.environ.get("ACESTEP_HOME", ".")
    dit_path, lm_path, dit_key = parse_variant(a.get("variant", "turbo+lm0.6B"))
    device = a.get("device", "cuda")
    dit = AceStepHandler()
    dit.initialize_service(project_root=root, config_path=dit_path, device=device)
    llm = LLMHandler()
    if lm_path:
        llm.initialize(checkpoint_dir=os.path.join(root, "checkpoints"), lm_model_path=lm_path, backend=a.get("lm_backend", "vllm"), device=device)
    STATE.update(dit=dit, llm=llm, dit_key=dit_key, has_lm=bool(lm_path))
    return {"loaded": a.get("variant"), "dit": dit_path, "lm": lm_path}


def generate(a: dict) -> dict:
    from acestep.inference import GenerationConfig, GenerationParams, generate_music
    if "dit" not in STATE:
        raise RunnerError("E_MODEL", "load a variant first")
    params = GenerationParams(**build_params(a, STATE["dit_key"], STATE["has_lm"]))
    config = GenerationConfig(batch_size=int(a.get("count", 1)), audio_format="wav", use_random_seed=a.get("seed", -1) < 0)
    os.makedirs(a["out_dir"], exist_ok=True)
    result = generate_music(STATE["dit"], STATE["llm"], params, config, save_dir=a["out_dir"])
    if not result.success:
        raise RunnerError("E_MODEL", "ACE-Step reported: %s" % result.error)
    return {"paths": [x["path"] for x in result.audios], "sample_rate": result.audios[0]["sample_rate"],
            "seed": result.audios[0]["params"].get("seed")}


def with_task(task: str):
    return lambda a: generate({**a, "task_type": task})


if __name__ == "__main__":
    serve({"load": load, "unload": lambda a: STATE.clear() or True, "ping": lambda a: "pong", "generate": generate,
           "cover": with_task("cover"), "repaint": with_task("repaint")})
