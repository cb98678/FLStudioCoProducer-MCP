from __future__ import annotations

import json
from pathlib import Path

import soundfile as sf

from coproducer import call, vocalchunk
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def join_vocal_chunks(manifest_path: str, out_path: str, suffix: str = "", shifts_16ths: dict | None = None) -> Result:
    """Lay the chunks of a manifest (split_vocal_phrases) back on one clock as a full-length file: each chunk file at its grid line, so
    the result is the source vocal with the chunks' edits in place (Newtime's fit; a chunk moved by shifts_16ths {index: 16ths}). suffix
    picks an edited copy of each chunk (STEM_NN{suffix}.wav, the chunk itself when the copy is missing): "_q" for
    quantize_vocal_chunks_gui's output. Writes out_path and reports the files used. Errors: E_SANDBOX_VIOLATION, E_IO.
    """
    root = str(get_service("sandbox_root"))
    mp, dst = call("check_sandbox_path", path=manifest_path, sandbox_root=root), call("check_sandbox_path", path=out_path, sandbox_root=root)
    if not mp.ok or not dst.ok:
        return mp if not mp.ok else dst
    try:
        man = json.loads(Path(mp.value["resolved"]).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return fail("E_IO", "cannot read the manifest: %s" % e)
    step = 60.0 / man["bpm"] / 4.0
    shifts = {int(k): float(v) for k, v in (shifts_16ths or {}).items()}
    files, starts, used = [], [], []
    for c in man["chunks"]:
        p = Path(c["file"])
        alt = p.with_name(p.stem + suffix + p.suffix) if suffix else p
        f = alt if alt.is_file() else p
        if not f.is_file():
            return fail("E_IO", "chunk file missing: %s" % p.name)
        files.append(str(f))
        starts.append(c["grid_s"] + shifts.get(c["index"], 0.0) * step)
        used.append({"index": c["index"], "file": f.name, "edited": f == alt and bool(suffix), "shift_16ths": shifts.get(c["index"], 0.0)})
    try:
        y = vocalchunk.assemble(files, starts, int(man["rate"]), float(man["duration_s"]) + 1.0)
        Path(dst.value["resolved"]).parent.mkdir(parents=True, exist_ok=True)
        sf.write(dst.value["resolved"], y, int(man["rate"]), subtype="PCM_24")
    except (OSError, ValueError) as e:
        return fail("E_IO", str(e))
    return ok({"out_path": dst.value["resolved"], "chunks": len(files), "edited": sum(1 for u in used if u["edited"]), "used": used})
