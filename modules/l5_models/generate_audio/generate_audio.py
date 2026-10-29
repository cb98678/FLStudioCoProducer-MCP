from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def generate_audio(prompt: str, out_dir: str, duration_s: float = 30.0, bpm: float = 0.0, key: str = "",
                   seed: int = -1) -> Result:
    """Generate instrumental audio from a text prompt with ACE-Step. Files are written inside the sandbox folder.

    bpm 0 and an empty key let the model choose. Output must pass a silence check before it is returned.
    """
    root = get_service("sandbox_root")
    chk = call("check_sandbox_path", path=out_dir, sandbox_root=str(root)) if root else fail("E_SANDBOX_VIOLATION", "no sandbox folder")
    if not chk.ok:
        return chk
    args = {"prompt": prompt, "out_dir": chk.value["resolved"], "duration": duration_s, "seed": seed, "instrumental": True}
    args.update({k: v for k, v in (("bpm", bpm), ("key", key)) if v})
    got = call("run_model_op", model="acestep", op="generate", args=args, timeout_s=1800)
    if not got.ok:
        return got
    for p in got.value["paths"]:
        quiet = call("detect_silence", path=p)
        if not quiet.ok or quiet.value["mostly_silent"]:
            return fail("E_NOT_VERIFIED", "generated audio is silent or unreadable", path=p)
    return ok(got.value, verified=True)
