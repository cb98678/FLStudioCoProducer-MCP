from __future__ import annotations

import json
from pathlib import Path

from coproducer import arranger, call, loopkit, soundbrief
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def write_support_parts(vocal_path: str, chords: list, bpm: float, bars: int, key_pc: int, sections: list, out_path: str, options: dict | None = None) -> Result:
    """Write the parts around a vocal as a session keyboardist and arranger would (skill session-arranger): a pad and a keys figure by
    phrase density, a bass on the sections' groove cells, an answer line only in her rests. Reads the vocal only for where she sings and
    how busy she is (options.vocal_notes, a pitch reading of her line, adds to that and sets her range); nothing heard is played. Writes
    out_path (JSON: parts, modes, cells, answers, check) and a MIDI file beside it. Errors: E_SANDBOX_VIOLATION, E_IO, E_ARG
    (an unknown cell, a chord name that does not parse), E_NOT_VERIFIED."""
    opt = options or {}
    root = str(get_service("sandbox_root"))
    chk = call("check_sandbox_path", path=out_path, sandbox_root=root)
    if not chk.ok:
        return chk
    if any("bar" not in c for c in chords) or any(len(s.get("bars") or ()) != 2 for s in sections):
        return fail("E_ARG", "every chord needs its bar (1-based) and every section its bars [first, end) (0-based)")
    bad = [s.get("cell") for s in sections if s.get("cell") not in arranger.CELLS] + [s["last"].get("cell") for s in sections if s.get("last") and s["last"].get("cell") not in arranger.CELLS]
    if bad:
        return fail("E_ARG", "unknown bass cell %s; cells: %s" % (bad[0], ", ".join(arranger.CELLS)))
    try:
        [arranger.parse_chord(c.get("chord")) for c in chords]
    except (ValueError, IndexError):
        return fail("E_ARG", "a chord name does not parse (root C to B, # or b, m, dim or 5)")
    try:
        x, rate = soundbrief.load_slice(vocal_path)
    except ValueError as e:
        return fail("E_IO", str(e))
    notes = [list(n) for n in opt.get("vocal_notes") or []]
    vm = arranger.vocal_map(x, rate, bpm, float(opt.get("origin_s", 0.0)), bars * 4, float(opt.get("floor_under_db", 30.0)))
    if notes:
        vm = arranger.merge_maps(vm, arranger.vocal_map_from_notes(notes, bars * 4))
    res = arranger.arrange(chords, bars, vm, arranger.voice_range(notes), key_pc, opt.get("mode", "major"), sections,
                           int(opt.get("answer_every", 2)), tuple(opt.get("soft_bars") or ()))
    out = Path(chk.value["resolved"])
    out.parent.mkdir(parents=True, exist_ok=True)
    rep = {k: res[k] for k in ("modes", "cells", "answers", "check")}
    out.write_text(json.dumps({**rep, "parts": res["parts"], "bpm": bpm, "sung_share": round(sum(vm["sung"]) / max(1, len(vm["sung"])), 3)}, default=float), encoding="utf-8")
    mid = loopkit.write_midi(out.with_suffix(".mid"), {k: v for k, v in res["parts"].items() if v}, bpm)
    back = json.loads(out.read_text(encoding="utf-8"))
    if {k: len(v) for k, v in back["parts"].items()} != {k: len(v) for k, v in res["parts"].items()} or not mid.is_file():
        return fail("E_NOT_VERIFIED", "the parts do not read back as written", path=str(out))
    return ok({"path": str(out), "midi": str(mid), "counts": {k: len(v) for k, v in res["parts"].items()}, **rep}, verified=True)
