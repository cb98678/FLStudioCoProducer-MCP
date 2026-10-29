from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from coproducer import call
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def prepare_rate_copy(path: str, out_path: str, up: int, down: int) -> Result:
    """Write a copy of an audio file resampled by up/down but labelled with the same sample rate, so it plays up/down times as long (and that
    much lower: 442/441 is 3.9 cents). Used around Newtime, whose grid sits on this machine's samples as if they ran at 44200 Hz: a 130 bpm
    vocal slowed by 442/441 lands on that grid, and 441/442 undoes it after quantizing. Errors: E_SANDBOX_VIOLATION, E_IO, E_ARG.
    """
    root = str(get_service("sandbox_root"))
    dst = call("check_sandbox_path", path=out_path, sandbox_root=root)
    if not dst.ok:
        return dst
    if not (1 <= up <= 10000 and 1 <= down <= 10000) or not (0.5 <= up / down <= 2.0):
        return fail("E_ARG", "up/down must be whole numbers 1..10000 with a ratio between 0.5 and 2")
    try:
        x, rate = sf.read(path, dtype="float64", always_2d=True)
    except (RuntimeError, OSError) as e:
        return fail("E_IO", "cannot read %s: %s" % (Path(path).name, e))
    y = np.stack([resample_poly(x[:, c], up, down) for c in range(x.shape[1])], axis=1) if up != down else x
    Path(dst.value["resolved"]).parent.mkdir(parents=True, exist_ok=True)
    sf.write(dst.value["resolved"], y.astype("float32"), rate, subtype="FLOAT")
    return ok({"out_path": dst.value["resolved"], "frames_in": int(x.shape[0]), "frames_out": int(y.shape[0]), "rate": int(rate),
               "ratio": round(y.shape[0] / max(1, x.shape[0]), 6)})
