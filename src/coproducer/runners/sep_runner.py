"""Vocal separation with a Mel-Band RoFormer checkpoint through python-audio-separator (runs inside models/envs/sep).

Measured listing on the host (audio-separator 0.47.1, 2026-10-25): vocals_mel_band_roformer.ckpt (Kimberley Jensen) leads its vocal table at
12.6 dB SDR, against 10.8 for htdemucs_ft and 9.9 for htdemucs. The checkpoint is a local file under models/weights/audio_separator, checked by
its hash before use; the worker never downloads (the listing call does reach the network, so it is not used here).
Sources: https://github.com/nomadkaraoke/python-audio-separator (MIT), https://mvsep.com/en/algorithms.
"""
from __future__ import annotations

import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner_common import RunnerError, serve  # noqa: E402

STATE: dict = {}


def _check(path: str, sha256: str) -> None:
    if not os.path.isfile(path):
        raise RunnerError("E_MODEL", "checkpoint missing: %s (run coproducer install-models sep)" % path)
    if sha256:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for block in iter(lambda: fh.read(1 << 20), b""):
                h.update(block)
        if h.hexdigest() != sha256:
            raise RunnerError("E_MODEL", "checkpoint %s does not match its pinned hash" % os.path.basename(path))


def load(a: dict) -> dict:
    return {"loaded": "sep"}


def vocals(a: dict) -> dict:
    """Split an audio file into vocals and the rest. args: path, out_dir, model_dir, model (file name), sha256. Returns {vocals, instrumental} paths."""
    from audio_separator.separator import Separator
    model, model_dir = a.get("model", "vocals_mel_band_roformer.ckpt"), a["model_dir"]
    key = (model_dir, model, a["out_dir"])
    if STATE.get("key") != key:
        _check(os.path.join(model_dir, model), a.get("sha256", ""))
        sep = Separator(model_file_dir=model_dir, output_dir=a["out_dir"], output_format="WAV", sample_rate=44100)
        sep.load_model(model)
        STATE["sep"], STATE["key"] = sep, key
    os.makedirs(a["out_dir"], exist_ok=True)
    stem = os.path.splitext(os.path.basename(a["path"]))[0]
    files = STATE["sep"].separate(a["path"], {"Vocals": stem + "_vocals", "Other": stem + "_instrumental", "Instrumental": stem + "_instrumental"})
    paths = [f if os.path.isabs(f) else os.path.join(a["out_dir"], f) for f in files]
    found = {("vocals" if p.endswith("_vocals.wav") else "instrumental"): p for p in paths}
    if set(found) != {"vocals", "instrumental"}:
        raise RunnerError("E_MODEL", "the separator wrote %s" % [os.path.basename(p) for p in paths])
    return found


if __name__ == "__main__":
    serve({"load": load, "unload": lambda a: STATE.clear() or True, "ping": lambda a: "pong", "vocals": vocals})
