from __future__ import annotations

from pathlib import Path

from coproducer import call
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def generate_cover(src_path: str, prompt: str, out_dir: str, strength: float = 0.7, seed: int = -1) -> Result:
    """Re-render a reference audio file in the style the prompt describes, keeping its melody and structure.

    strength 1.0 stays closest to the source; lower values follow the prompt more. Output goes inside the sandbox folder.
    """
    root = get_service("sandbox_root")
    chk = call("check_sandbox_path", path=out_dir, sandbox_root=str(root)) if root else fail("E_SANDBOX_VIOLATION", "no sandbox folder")
    if not chk.ok:
        return chk
    if not Path(src_path).is_file():
        return fail("E_NOT_FOUND", "no audio file at %s" % Path(src_path).name)
    args = {"src_audio": src_path, "prompt": prompt, "out_dir": chk.value["resolved"], "strength": strength, "seed": seed}
    got = call("run_model_op", model="acestep", op="cover", args=args, timeout_s=1800)
    if not got.ok:
        return got
    quiet = call("detect_silence", path=got.value["paths"][0])
    if not quiet.ok or quiet.value["mostly_silent"]:
        return fail("E_NOT_VERIFIED", "the cover is silent or unreadable")
    return ok(got.value, verified=True)
