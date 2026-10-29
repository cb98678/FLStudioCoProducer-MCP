from __future__ import annotations

import time
from pathlib import Path

import numpy as np
from PIL import Image

from coproducer import call, knobread
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def _cfg() -> dict:
    return get_service("desktop_config") or {}


def _poll(check, timeout_s: float):
    end = time.monotonic() + timeout_s * _cfg().get("timeout_scale", 1.0)
    while True:
        got = check()
        if got or time.monotonic() >= end:
            return got
        time.sleep(0.05)


def _titles(contains: str) -> list:
    got = call("list_open_dialogs")
    return [d["title"] for d in got.value["dialogs"] if contains.lower() in d["title"].lower()] if got.ok else []


def _click(s: dict, p: dict) -> Result:
    a = (_cfg().get("anchors") or {}).get(s.get("anchor", ""))
    if a is None:
        return fail("E_GUI_MISMATCH", "anchor %r is not recorded; run coproducer calibrate" % s.get("anchor"))
    return call("click_at", x=a[0], y=a[1])


def _click_row(s: dict, p: dict) -> Result:
    """Click an anchor moved down by whole rows (playlist tracks): row 1 is the anchor itself, each further row adds s["dy"] pixels."""
    a = (_cfg().get("anchors") or {}).get(s.get("anchor", ""))
    if a is None:
        return fail("E_GUI_MISMATCH", "anchor %r is not recorded; run coproducer calibrate" % s.get("anchor"))
    return call("click_at", x=a[0], y=round(a[1] + s["dy"] * (int(p[s["param"]]) - 1)))


def _click_col(s: dict, p: dict) -> Result:
    """Click an anchor moved right by whole columns (mixer strips): column 1 is the anchor itself, each further column adds s["dx"] pixels. Optional button."""
    a = (_cfg().get("anchors") or {}).get(s.get("anchor", ""))
    if a is None:
        return fail("E_GUI_MISMATCH", "anchor %r is not recorded; run coproducer calibrate" % s.get("anchor"))
    return call("click_at", x=round(a[0] + s["dx"] * (int(p[s["param"]]) - 1)), y=a[1], button=s.get("button", "left"))


def _template_click(s: dict, p: dict) -> Result:
    """Click the centre of a stored interface picture found on a fresh screenshot (menu entries move between projects), or dx, dy pixels
    from it (a clip's menu icon found by its icon and name)."""
    root = get_service("sandbox_root")
    shot = call("take_screenshot", out_path=str(root) + "/screens/_template.png") if root is not None else fail("E_SANDBOX_VIOLATION", "no sandbox folder")
    if not shot.ok:
        return shot
    at = call("locate_template", image_path=shot.value["path"], template_name=s["template"].format(**p), min_score=s.get("min_score", 0.9))
    return at if not at.ok else call("click_at", x=at.value["x"] + int(s.get("dx", 0)), y=at.value["y"] + int(s.get("dy", 0)))


def _window_point(s: dict, p: dict) -> Result:
    """A point at an offset from the top-left corner of an FL window found by its title, in FL main-window pixels."""
    got, ready = call("list_open_dialogs"), call("check_desktop_ready")
    if not got.ok or not ready.ok:
        return got if not got.ok else ready
    hit = next((d for d in got.value["dialogs"] if s["title"].format(**p).lower() in d["title"].lower() and len(d.get("rect") or []) == 4), None)
    if hit is None:
        return fail("E_GUI_MISMATCH", "no FL window titled %r is open" % s["title"].format(**p))
    dy = s["dy"] + round(s.get("dy_each", 0) * (int(p[s["param"]]) - 1)) if "param" in s else s["dy"]
    return ok({"x": hit["rect"][0] + s["dx"] - ready.value["left"], "y": hit["rect"][1] + dy - ready.value["top"], "height": ready.value["height"]})


def _click_in_window(s: dict, p: dict) -> Result:
    """Click at an offset from the top-left corner of an FL window found by its title (plugin and channel windows open where they were last
    left). Optional button, clicks and modifiers (["shift"] adds a Newtime warp marker)."""
    at = _window_point(s, p)
    if not at.ok:
        return at
    extra = {"modifiers": s["modifiers"]} if s.get("modifiers") else {}
    return call("click_at", x=at.value["x"], y=at.value["y"], button=s.get("button", "left"), clicks=int(s.get("clicks", 1)), **extra)


def _knob_in_window(s: dict, p: dict) -> Result:
    """Turn a knob found from a window's position to `value` (0..1 of its travel): read its arc on a screenshot, drag, read again. Knob
    drags are not linear in pixels, so one drag is never trusted. Optional tol (0.03), tries (8), px_per_travel (200)."""
    at, root = _window_point(s, p), get_service("sandbox_root")
    if not at.ok:
        return at
    x, y, target = at.value["x"], at.value["y"], float(str(s["value"]).format(**p))
    for _ in range(int(s.get("tries", 8))):
        shot = call("take_screenshot", out_path=str(root) + "/screens/_knob.png")
        if not shot.ok:
            return shot
        now = knobread.knob_value(np.asarray(Image.open(shot.value["path"]).convert("RGB")), x, y)
        if abs(now - target) <= float(s.get("tol", 0.03)):
            return ok({"value": now})
        y2 = min(max(1, y + knobread.drag_pixels(now, target, float(s.get("px_per_travel", 200.0)))), at.value["height"] - 2)
        call("drag_between", x1=x, y1=y, x2=x, y2=y2, seconds=0.5)
    return fail("E_NOT_VERIFIED", "the knob at (%d, %d) did not reach %.2f (it reads %.2f)" % (x, y, target, now))


def _locate_click(s: dict, p: dict) -> Result:
    at = call("locate_element", description=s["description"].format(**p))
    return at if not at.ok else call("click_at", x=at.value["x"] + int(s.get("dx", 0)), y=at.value["y"] + int(s.get("dy", 0)))


def _expect_dialog(s: dict, p: dict) -> Result:
    want = s.get("contains", "").format(**p)
    hit = _poll(lambda: _titles(want), s.get("timeout_s", 5))
    return ok(hit) if hit else fail("E_GUI_MISMATCH", "no dialog containing %r appeared" % want)


def _expect_no_dialog(s: dict, p: dict) -> Result:
    left = _poll(lambda: not _titles(""), s.get("timeout_s", 5))
    return ok(True) if left else fail("E_BLOCKED_BY_DIALOG", "a dialog is still open", dialogs=_titles(""))


def _expect_title(s: dict, p: dict) -> Result:
    want = s["contains"].format(**p).lower()
    hit = _poll(lambda: want in call("check_desktop_ready").value["title"].lower(), s.get("timeout_s", 5))
    return ok(True) if hit else fail("E_GUI_MISMATCH", "the window title does not contain %r" % want)


def _expect_file(s: dict, p: dict) -> Result:
    target = Path(s["path"].format(**p))
    hit = _poll(lambda: target.is_file() and target.stat().st_size > 0, s.get("timeout_s", 5))
    return ok(True) if hit else fail("E_NOT_VERIFIED", "the expected file did not appear: %s" % target.name)


_STEPS = {
    "hotkey": lambda s, p: call("press_hotkey", keys=s["keys"]),
    "type": lambda s, p: call("type_text", text=s["text"].format(**p)),
    "wait": lambda s, p: (time.sleep(s["seconds"] * _cfg().get("timeout_scale", 1.0)), ok(True))[1],
    "click": _click, "click_row": _click_row, "click_col": _click_col, "template_click": _template_click, "click_in_window": _click_in_window,
    "knob_in_window": _knob_in_window, "locate_click": _locate_click, "expect_dialog": _expect_dialog, "expect_no_dialog": _expect_no_dialog,
    "expect_title": _expect_title, "expect_file": _expect_file,
}


def _failed(name: str, i: int, step: dict, res: Result) -> Result:
    root, shot = get_service("sandbox_root"), None
    if root is not None and res.error.code not in ("E_HALTED", "E_UNSUPPORTED_API"):
        Path(str(root), "screens").mkdir(parents=True, exist_ok=True)
        got = call("take_screenshot", out_path=str(root) + "/screens/failed_%s.png" % name)
        shot = got.value["path"] if got.ok else None
    return fail(res.error.code, "recipe %s stopped at step %d (%s): %s" % (name, i + 1, step["do"], res.error.message),
                recipe=name, step=i + 1, kind=step["do"], screenshot=shot)


def run_gui_recipe(name: str, params: dict | None = None) -> Result:
    """Run a named GUI recipe step by step. It stops at the first step or check that fails and saves a screenshot.

    Draft recipes (verified false) only run when config desktop.allow_unverified is true.
    A recipe marked needs_sandbox_project first checks that a sandbox project is open. Errors: E_UNSUPPORTED_API, E_ARG, E_SANDBOX_VIOLATION.
    """
    rec = call("load_gui_recipe", name=name)
    if not rec.ok:
        return rec
    r, p = rec.value, params or {}
    if not r["verified"] and not _cfg().get("allow_unverified"):
        return fail("E_UNSUPPORTED_API", "recipe %s is a draft that has not been confirmed on this machine; run coproducer calibrate %s" % (name, name))
    if r.get("needs_sandbox_project"):
        guard = call("check_sandbox_project_open")
        if not guard.ok:
            return guard
        allowed = [a.lower() for a in r.get("allow_open", [])]          # editor windows the recipe works in (Newtime, Newtone)
        blocking = [t for t in _titles("") if not any(a in t.lower() for a in allowed)]
        if blocking:
            return fail("E_BLOCKED_BY_DIALOG", "a dialog is open in FL (%s); close it first, nothing was clicked" % ", ".join(blocking))
    missing = [k for k in r["params"] if k not in p]
    if missing:
        return fail("E_ARG", "recipe %s needs parameters %s" % (name, ", ".join(missing)))
    for i, step in enumerate(r["steps"]):
        res = _STEPS[step["do"]](step, p)
        if not res.ok:
            return _failed(name, i, step, res)
    return ok({"recipe": name, "steps_run": len(r["steps"])}, unverified_recipe=not r["verified"])
