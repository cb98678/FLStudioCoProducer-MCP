"""Demucs stem separation. Runs inside the demucs environment (pip install demucs; the maintained fork is adefossez/demucs).

Docs checked 2026-10-18: https://github.com/adefossez/demucs and https://github.com/facebookresearch/demucs (archived).
The CLI entry demucs.separate.main(argv) is the documented way to call it from Python. The -o flag is not shown on the
README, so the smoke test confirms it; stems are found by searching the output folder either way.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner_common import RunnerError, serve  # noqa: E402

STEMS_BY_MODEL = {"htdemucs": ("drums", "bass", "other", "vocals"), "htdemucs_ft": ("drums", "bass", "other", "vocals"),
                  "htdemucs_6s": ("drums", "bass", "other", "vocals", "guitar", "piano")}


def build_args(input_path: str, out_dir: str, model: str, two_stem: str = "", device: str = "") -> list[str]:
    """Command line for demucs.separate.main. Output is 24-bit WAV."""
    args = ["-n", model, "-o", out_dir, "--int24"]
    if two_stem:
        args += ["--two-stems", two_stem]
    if device:
        args += ["-d", device]
    return args + [input_path]


def find_stems(out_dir: str, model: str, track: str) -> dict:
    """Collect <out_dir>/<model>/<track>/<stem>.wav into {stem: path}."""
    folder = os.path.join(out_dir, model, track)
    if not os.path.isdir(folder):
        raise RunnerError("E_MODEL", "demucs wrote no folder for this track", expected=folder)
    return {os.path.splitext(f)[0]: os.path.join(folder, f) for f in sorted(os.listdir(folder)) if f.lower().endswith(".wav")}


def separate(a: dict) -> dict:
    import demucs.separate
    model = a.get("model", "htdemucs")
    args = build_args(a["input_path"], a["out_dir"], model, a.get("two_stem", ""), a.get("device", ""))
    try:
        demucs.separate.main(args)
    except SystemExit as e:
        if e.code not in (0, None):
            raise RunnerError("E_MODEL", "demucs exited with %s" % e.code) from e
    track = os.path.splitext(os.path.basename(a["input_path"]))[0]
    return {"stems": find_stems(a["out_dir"], model, track), "model": model}


if __name__ == "__main__":
    serve({"load": lambda a: {"loaded": a.get("variant")}, "unload": lambda a: True, "ping": lambda a: "pong", "separate": separate})
