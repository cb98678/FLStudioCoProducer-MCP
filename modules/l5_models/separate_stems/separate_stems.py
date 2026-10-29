from __future__ import annotations

from pathlib import Path

from coproducer import call
from coproducer.result import Result, fail, ok
from coproducer.services import get_service

_MODELS = {2: "htdemucs", 4: "htdemucs", 6: "htdemucs_6s"}


def separate_stems(input_path: str, out_dir: str, stems: int = 4, two_stem: str = "", quality: str = "fast") -> Result:
    """Split an audio file into stems with Demucs. stems is 2, 4 or 6; two_stem names the stem kept when stems is 2.

    quality 'high' uses the fine-tuned 4-stem model (about four times slower). Output goes inside the sandbox folder.
    """
    root = get_service("sandbox_root")
    chk = call("check_sandbox_path", path=out_dir, sandbox_root=str(root)) if root else fail("E_SANDBOX_VIOLATION", "no sandbox folder")
    if not chk.ok:
        return chk
    if not Path(input_path).is_file():
        return fail("E_NOT_FOUND", "no audio file at %s" % Path(input_path).name)
    model = "htdemucs_ft" if quality == "high" and stems == 4 else _MODELS[stems]
    if stems == 2 and not two_stem:
        return fail("E_ARG", "two_stem is required when stems is 2")
    got = call("run_model_op", model="demucs", op="separate", timeout_s=1800,
               args={"input_path": input_path, "out_dir": chk.value["resolved"], "model": model, "two_stem": two_stem})
    if not got.ok:
        return got
    missing = [n for n, p in got.value["stems"].items() if not Path(p).is_file()]
    return fail("E_NOT_VERIFIED", "stems missing on disk: %s" % ", ".join(missing)) if missing else ok(got.value, verified=True)
