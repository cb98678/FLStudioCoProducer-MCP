from __future__ import annotations

from pathlib import Path

from coproducer import call, serumspec, soundbrief, wavetables
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def build_wavetable(out_path: str, path: str = "", formula: str = "", options: dict | None = None) -> Result:
    """Write a Serum 2 wavetable to out_path (a WAV in the sandbox): from path, the longest held note in it (options start_s, end_s)
    read pitch-synchronously into options.frames cycles (default 16) from its attack side to its tail; or from formula, Serum's formula
    parser variables (x, w, y). Returns the osc settings for serum-mcp (sample_source and sample_frames), the pitch, and edge_loss_db.
    Errors: E_ARG (neither or both sources, a bad formula), E_IO, E_NOT_FOUND (no held pitch), E_SANDBOX_VIOLATION, E_NOT_VERIFIED."""
    opt = options or {}
    chk = call("check_sandbox_path", path=out_path, sandbox_root=str(get_service("sandbox_root")))
    if not chk.ok:
        return chk
    if bool(path) == bool(formula):
        return fail("E_ARG", "give path or formula, one of them")
    frames = int(opt.get("frames", 16))
    try:
        if formula:
            t = wavetables.formula(formula, frames)
            t["frames"] = wavetables.turn_quiet(t["frames"])
            t["edge_loss_db"] = round(wavetables.edge_loss_db(t["frames"]), 1)
        else:
            x, rate = soundbrief.load_slice(path, float(opt.get("start_s", 0.0)), float(opt.get("end_s", 0.0)))
            t = wavetables.cycles(wavetables.mono(x), rate, frames, float(opt.get("fmin", 30.0)), float(opt.get("fmax", 1500.0)),
                                  int(opt.get("periods", 4)), float(opt.get("f0_hz", 0.0)))
    except (SyntaxError, wavetables.TableError) as e:
        return fail("E_NOT_FOUND" if "no held pitch" in str(e) else "E_ARG", str(e))
    except ValueError as e:
        return fail("E_IO", str(e))
    out = wavetables.write_table(out_path, t["frames"])
    back, clm = wavetables.read_table(out)
    same = clm and len(back) == frames and max(float(abs(a - b).max()) for a, b in zip(back, t["frames"])) < 1e-6
    if not same:
        return fail("E_NOT_VERIFIED", "the table does not read back as written", path=str(out))
    rep = {k: v for k, v in t.items() if k != "frames"}
    return ok({"path": str(Path(out)), "frames": frames, "oscillator": serumspec.table_osc(str(Path(out)), frames), **rep}, verified=True)
