"""Music analysis models in the mir environment: beats and downbeats (beat_this), vocal pitch (torchcrepe) and, when installed, music
embeddings (MuQ-MuLan). Runs inside models/envs/mir.

Sources checked 2026-10-25: https://github.com/CPJKU/beat_this (MIT code and weights, ISMIR 2024), https://github.com/maxrmorrison/torchcrepe
(MIT, weights in the wheel), https://github.com/tencent-ailab/MuQ (code MIT, weights CC-BY-NC 4.0). The beat_this checkpoint is read from a local
file that install-models downloaded and hashed (stacks.STACKS["mir"]["files"]), so this worker never fetches anything.
"""
from __future__ import annotations

import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner_common import RunnerError, serve  # noqa: E402

STATE: dict = {}


def _device() -> str:
    import torch
    return "cuda" if torch.cuda.is_available() else "cpu"


def _checked(path: str, sha256: str) -> str:
    if not path or not os.path.isfile(path):
        raise RunnerError("E_MODEL", "checkpoint missing: %s (run coproducer install-models mir)" % path)
    if sha256:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for block in iter(lambda: fh.read(1 << 20), b""):
                h.update(block)
        if h.hexdigest() != sha256:
            raise RunnerError("E_MODEL", "checkpoint %s does not match its pinned hash" % os.path.basename(path))
    return path


def load(a: dict) -> dict:
    STATE["device"] = a.get("device") or _device()
    STATE["beat_ckpt"] = a.get("beat_checkpoint", "")
    STATE["beat_sha"] = a.get("beat_sha256", "")
    return {"loaded": "mir", "device": STATE["device"]}


def beats(a: dict) -> dict:
    """{"beats": [s...], "downbeats": [s...]} for an audio file."""
    from beat_this.inference import File2Beats
    if "file2beats" not in STATE:
        ckpt = _checked(a.get("checkpoint") or STATE.get("beat_ckpt", ""), a.get("sha256") or STATE.get("beat_sha", ""))
        STATE["file2beats"] = File2Beats(checkpoint_path=ckpt, device=STATE.get("device") or _device(), dbn=False)
    b, d = STATE["file2beats"](a["path"])
    return {"beats": [round(float(x), 4) for x in b], "downbeats": [round(float(x), 4) for x in d]}


def melody(a: dict) -> dict:
    """Frame-wise f0 and periodicity of a (mostly monophonic) vocal stem with torchcrepe. hop_ms 10 by default."""
    import librosa
    import numpy as np
    import torch
    import torchcrepe
    sr = 16000
    x, _ = librosa.load(a["path"], sr=sr, mono=True, offset=float(a.get("offset_s", 0.0)), duration=a.get("duration_s"))
    hop = int(sr * float(a.get("hop_ms", 10)) / 1000)
    audio = torch.tensor(x, dtype=torch.float32)[None]
    f0, per = torchcrepe.predict(audio, sr, hop, float(a.get("fmin", 65.0)), float(a.get("fmax", 1000.0)), a.get("model", "full"),
                                 batch_size=512, device=STATE.get("device") or _device(), return_periodicity=True)
    per = torchcrepe.filter.median(per, 3)
    f0 = torchcrepe.filter.mean(f0, 3)
    f = f0[0].cpu().numpy()
    p = per[0].cpu().numpy()
    rms = librosa.feature.rms(y=x, frame_length=hop * 4, hop_length=hop, center=True)[0][: len(f)]
    return {"hop_s": hop / sr, "offset_s": float(a.get("offset_s", 0.0)), "f0": [round(float(v), 2) for v in f],
            "periodicity": [round(float(v), 3) for v in p], "rms": [round(float(v), 5) for v in np.pad(rms, (0, max(0, len(f) - len(rms))))]}


def embed(a: dict) -> dict:
    """MuQ-MuLan embeddings (512 values, unit length) for windows of an audio file: segments [[start_s, end_s], ...]."""
    import librosa
    import torch
    if "mulan" not in STATE:
        try:
            from muq import MuQMuLan
        except ImportError as e:
            raise RunnerError("E_MODEL", "MuQ-MuLan is not installed in the mir environment") from e
        repo = a.get("repo", "OpenMuQ/MuQ-MuLan-large")
        for name, rev in (a.get("snapshots") or {}).items():  # the offline cache must hold the pinned snapshots (stacks "hf_snapshots")
            ref = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub", "models--" + name.replace("/", "--"), "refs", "main")
            if not os.path.isfile(ref) or open(ref, encoding="utf-8").read().strip() != rev:
                raise RunnerError("E_MODEL", "the cached %s is not the pinned snapshot %s" % (name, rev[:10]))
        STATE["mulan"] = MuQMuLan.from_pretrained(repo).to(STATE.get("device") or _device()).eval()
    model = STATE["mulan"]
    x, _ = librosa.load(a["path"], sr=24000, mono=True)
    out = []
    for s, e in a.get("segments") or [[0, len(x) / 24000]]:
        seg = torch.tensor(x[int(s * 24000) : int(e * 24000)], dtype=torch.float32)[None].to(model.device)
        with torch.no_grad():
            v = model(wavs=seg)[0]
        v = v / v.norm()
        out.append([round(float(t), 6) for t in v.cpu()])
    return {"embeddings": out}


if __name__ == "__main__":
    serve({"load": load, "unload": lambda a: STATE.clear() or True, "ping": lambda a: "pong", "beats": beats, "melody": melody, "embed": embed})
