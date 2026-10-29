from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

from coproducer import call, dsp
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def _matched(path: str, target: float, ceiling_db: float) -> tuple[np.ndarray, int, dict]:
    x, rate = dsp.load_audio(path)
    before = dsp.integrated_loudness(x, rate)
    gain = min(target - before, 0.0 if target <= before else target - before)
    peak = dsp.db(dsp.true_peak(x * 10 ** (gain / 20), rate))
    if peak > ceiling_db:
        gain -= peak - ceiling_db
    y = x * 10 ** (gain / 20)
    return y, rate, {"lufs_before": round(before, 2), "gain_db": round(gain, 2),
                     "lufs_after": round(dsp.integrated_loudness(y, rate), 2), "true_peak_db": round(dsp.db(dsp.true_peak(y, rate)), 2)}


def build_ab_package(a_path: str, b_path: str, out_dir: str, target_lufs: float | None = None, ceiling_db: float = -1.0) -> Result:
    """Write two copies matched to the same integrated loudness, so louder never sounds better.

    By default both are matched to the quieter file (gain only goes down). Errors: E_SANDBOX_VIOLATION, E_IO.
    """
    root = get_service("sandbox_root")
    chk = call("check_sandbox_path", path=out_dir, sandbox_root=str(root)) if root else fail("E_SANDBOX_VIOLATION", "no sandbox folder")
    if not chk.ok:
        return chk
    try:
        levels = [dsp.integrated_loudness(*dsp.load_audio(p)) for p in (a_path, b_path)]
        target = min(levels) if target_lufs is None else target_lufs
        outs = {k: _matched(p, target, ceiling_db) for k, p in (("A", a_path), ("B", b_path))}
        base = chk.value["resolved"]
        Path(base).mkdir(parents=True, exist_ok=True)
        paths = {}
        for k, (y, rate, info) in outs.items():
            paths[k] = "%s/ab_%s.wav" % (base, k)
            sf.write(paths[k], y, rate, subtype="PCM_24")
    except (ValueError, OSError, RuntimeError) as e:
        return fail("E_IO", "cannot build the A/B files: %s" % e)
    return ok({"paths": paths, "target_lufs": round(target, 2), "report": {k: v[2] for k, v in outs.items()}})
