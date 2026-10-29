from __future__ import annotations

from pathlib import Path

from coproducer import call
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def separate_stems_hq(input_path: str, out_dir: str, quality: str = "high") -> Result:
    """Four stems with the best open vocal model in front: Mel-Band RoFormer splits vocals from the rest (12.6 dB vocal SDR in audio-separator's
    table, against 10.8 for htdemucs_ft), then Demucs splits the instrumental into drums, bass and other (quality high is htdemucs_ft). The Demucs
    vocal output, which is only bleed after the first pass, is left out. On a mix summed from the Friends stems (2026-10-25) the RoFormer vocal
    measured 9.6 dB SDR against the true vocal. Errors: E_SANDBOX_VIOLATION, E_NOT_FOUND, E_MODEL, E_NOT_VERIFIED.
    """
    chk = call("check_sandbox_path", path=out_dir, sandbox_root=str(get_service("sandbox_root")))
    if not chk.ok:
        return chk
    if not Path(input_path).is_file():
        return fail("E_NOT_FOUND", "no audio file at %s" % Path(input_path).name)
    m = (get_service("model_files") or {}).get("roformer_vocals", {})
    out = Path(chk.value["resolved"])
    first = call("run_model_op", model="roformer", op="vocals", timeout_s=1800,
                 args={"path": input_path, "out_dir": str(out / "roformer"), "model_dir": m.get("model_dir", ""), "model": m.get("model", "vocals_mel_band_roformer.ckpt"),
                       "sha256": m.get("sha256", "")})
    if not first.ok:
        return first
    rest = call("separate_stems", input_path=first.value["instrumental"], out_dir=str(out / "demucs"), stems=4, quality=quality)
    if not rest.ok:
        return rest
    stems = {"vocals": first.value["vocals"], "drums": rest.value["stems"]["drums"], "bass": rest.value["stems"]["bass"],
             "other": rest.value["stems"]["other"], "instrumental": first.value["instrumental"]}
    missing = [k for k, p in stems.items() if not Path(p).is_file()]
    if missing:
        return fail("E_NOT_VERIFIED", "stems missing on disk: %s" % ", ".join(missing))
    return ok({"stems": stems, "models": {"vocals": m.get("model", ""), "rest": rest.value["model"]}}, verified=True)
