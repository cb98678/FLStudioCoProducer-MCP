"""Verifiers: small checks that prove a step did what it claimed. Each returns ok on pass, E_NOT_VERIFIED on fail."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from ..result import Result, fail, ok
from .paths import walk_path


@dataclass
class VerifyCtx:
    call: Callable[..., Result]
    collab: Any = None
    original_ok: Callable[[], Result] | None = None
    extra: dict = field(default_factory=dict)


def _no(msg: str, **detail: Any) -> Result:
    return fail("E_NOT_VERIFIED", msg, **detail)


def _none(step, res, v, ctx) -> Result:
    return ok(True)


def _readback(step, res, v, ctx) -> Result:
    return ok(True) if res.meta.get("verified") is True else _no("the write did not report a verified readback")


def _file_nonempty(step, res, v, ctx) -> Result:
    got = walk_path(res.to_dict(), v.get("path", "value.path"))
    if not got.ok:
        return _no("result has no file path", path=v.get("path", "value.path"))
    p = Path(str(got.value))
    return ok(True) if p.is_file() and p.stat().st_size >= v.get("min_bytes", 16) else _no("file missing or too small", file=p.name)


def _measure_within(step, res, v, ctx) -> Result:
    got = walk_path(res.to_dict(), v.get("path", ""))
    if not got.ok or not isinstance(got.value, (int, float)):
        return _no("metric not found or not a number", path=v.get("path"))
    lo, hi = v.get("min", float("-inf")), v.get("max", float("inf"))
    return ok(got.value) if lo <= got.value <= hi else _no("%s is %s, outside %s to %s" % (v.get("path"), got.value, lo, hi))


def _stems_not_silent(step, res, v, ctx) -> Result:
    stems = walk_path(res.to_dict(), v.get("path", "value.stems"))
    if not stems.ok or not isinstance(stems.value, dict):
        return _no("result has no stems mapping")
    for name, path in stems.value.items():
        s = ctx.call("detect_silence", path=path)
        if not s.ok or s.value["mostly_silent"]:
            return _no("stem %s is silent or unreadable" % name, stem=name)
    return ok(True)


def _key_match(step, res, v, ctx) -> Result:
    a, b = ctx.call("estimate_key_dsp", path=v["a"]), ctx.call("estimate_key_dsp", path=v["b"])
    if not (a.ok and b.ok):
        return _no("could not estimate a key")
    same = a.value["key"] == b.value["key"]
    return ok([a.value["key"], b.value["key"]]) if same else _no("keys differ: %s and %s" % (a.value["key"], b.value["key"]))


def _bpm_match(step, res, v, ctx) -> Result:
    got = ctx.call("estimate_bpm_dsp", path=v["path"])
    if not got.ok:
        return _no("could not estimate tempo")
    want, tol, bpm = v["bpm"], v.get("tolerance", 2.0), got.value["bpm"]
    options = [bpm, bpm * 2, bpm / 2] if v.get("allow_octave") else [bpm]
    return ok(bpm) if any(abs(o - want) <= tol for o in options) else _no("tempo %s is not within %s of %s" % (bpm, tol, want))


def _melody_similarity(step, res, v, ctx) -> Result:
    got = ctx.call("compare_note_sequences", a=v["a"], b=v["b"])
    if not got.ok:
        return _no("could not compare melodies")
    need = v.get("min", 0.7)
    return ok(got.value["melody"]) if got.value["melody"] >= need else _no("melody score %s is under %s" % (got.value["melody"], need))


def _screenshot_post(step, res, v, ctx) -> Result:
    got = ctx.call("screenshot_verify", **v)
    return ok(True) if got.ok else fail("E_GUI_MISMATCH", "screenshot check failed or unavailable", **got.error.detail)


def _original_untouched(step, res, v, ctx) -> Result:
    if ctx.original_ok is None:
        return _no("no original hash is recorded")
    got = ctx.original_ok()
    return ok(True) if got.ok else _no("the original project changed", **got.error.detail)


def _human_review(step, res, v, ctx) -> Result:
    if ctx.collab is None:
        return fail("E_PENDING_HUMAN", "human review needs a collaborator")
    return ctx.collab.approve("review %s" % step["id"], {"value": res.value})


VERIFIERS: dict[str, Callable[..., Result]] = {
    "none": _none, "readback": _readback, "file_nonempty": _file_nonempty, "measure_within": _measure_within,
    "stems_not_silent": _stems_not_silent, "key_match": _key_match, "bpm_match": _bpm_match,
    "melody_similarity": _melody_similarity, "screenshot_post": _screenshot_post,
    "original_untouched": _original_untouched, "human_review": _human_review,
}
VERIFIER_NAMES = tuple(VERIFIERS)


def run_verifier(step: dict, res: Result, verify: dict, ctx: VerifyCtx) -> Result:
    fn = VERIFIERS.get(step.get("verifier", ""))
    if fn is None:
        return _no("unknown verifier %r" % step.get("verifier"))
    try:
        return fn(step, res, verify, ctx)
    except Exception as e:  # noqa: BLE001 - a verifier bug must be a failed check, not a crash
        return fail("E_INTERNAL", "verifier %s raised %s: %s" % (step.get("verifier"), type(e).__name__, e))
