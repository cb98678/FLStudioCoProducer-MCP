from __future__ import annotations

from pathlib import Path

from coproducer import call
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def repaint_section(src_path: str, start_s: float, end_s: float, prompt: str, out_dir: str, seed: int = -1) -> Result:
    """Regenerate one time range of an audio file with ACE-Step and keep the rest. Output goes inside the sandbox folder.

    Errors: E_ARG when end_s is not after start_s.
    """
    root = get_service("sandbox_root")
    chk = call("check_sandbox_path", path=out_dir, sandbox_root=str(root)) if root else fail("E_SANDBOX_VIOLATION", "no sandbox folder")
    if not chk.ok:
        return chk
    if end_s <= start_s:
        return fail("E_ARG", "end_s must be after start_s")
    if not Path(src_path).is_file():
        return fail("E_NOT_FOUND", "no audio file at %s" % Path(src_path).name)
    args = {"src_audio": src_path, "prompt": prompt, "out_dir": chk.value["resolved"], "start_s": start_s, "end_s": end_s, "seed": seed}
    got = call("run_model_op", model="acestep", op="repaint", args=args, timeout_s=1800)
    if not got.ok:
        return got
    quiet = call("detect_silence", path=got.value["paths"][0])
    return ok(got.value, verified=True) if quiet.ok and not quiet.value["mostly_silent"] else fail("E_NOT_VERIFIED", "the result is silent or unreadable")
