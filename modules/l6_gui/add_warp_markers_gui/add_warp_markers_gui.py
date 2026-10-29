from __future__ import annotations

import time

import numpy as np
from PIL import Image

from coproducer import call, newtimeview
from coproducer.result import Result, fail, ok
from coproducer.services import get_service

# Newtime's window at its default size (741 x 617 px), offsets from its top-left corner, measured on FL 26.1.7 at 2560 x 1440 (2026-10-29).
SIZE = (741, 617)
EDITOR = (6, 734)          # columns of the wave editor
BAND = (143, 188)          # rows above the waveform where the grid lines are plain
WAVE = (198, 578)          # rows the waveform is drawn in (also where marker lines are looked for)
SCROLL_ROW, TRACK = 600, (26, 714)   # the handle runs between the two arrow buttons; it and the buttons share one grey
LEFT_ARROW = 16                      # one click on it scrolls the view back about 16 px
CLICK_Y = 378
EDGE_PX = 50            # a Shift+click closer than about 25 px to the editor's edge scrolls the view 15 px; 50 px does not
STEP_BACK = 7           # left-arrow clicks after each page (7 x 16 px), so pages overlap by more than both edges
# A view is read from its bar lines (scale, and time within a bar) and its drawn waveform (which bar). Scrolling is by page: a click on the
# far end of the track moves one view width, then STEP_BACK clicks on the left arrow make the pages overlap. Markers are only clicked
# EDGE_PX inside the editor: a Shift+click near its edge scrolls the view 15 px, which put whole views of markers 100 ms early on
# 2026-10-29. Dragging the handle was not repeatable (Newtime's timeline runs about twice the sample and drags overshot).


def _look(title: str, approx_s: float, bar_s: float, peaks: np.ndarray, search_bars: int | None = 2, min_start_s: float | None = None) -> Result:
    """Screenshot, find the Newtime window, read its view (time at the editor's left edge, pixels per second) and its markers and handle."""
    ready, dl = call("check_desktop_ready"), call("list_open_dialogs")
    if not ready.ok or not dl.ok:
        return ready if not ready.ok else dl
    hit = next((d for d in dl.value["dialogs"] if title.lower() in d["title"].lower() and len(d.get("rect") or []) == 4), None)
    if hit is None:
        return fail("E_GUI_MISMATCH", "no Newtime window (title containing %r) is open" % title)
    r = hit["rect"]
    if (r[2] - r[0], r[3] - r[1]) != SIZE:
        return fail("E_GUI_MISMATCH", "Newtime is %dx%d, not its default %dx%d; restore the window size" % (r[2] - r[0], r[3] - r[1], *SIZE))
    ox, oy = r[0] - ready.value["left"], r[1] - ready.value["top"]
    shot = call("take_screenshot", out_path=str(get_service("sandbox_root")) + "/screens/_warp_markers.png")
    if not shot.ok:
        return shot
    rgb = np.asarray(Image.open(shot.value["path"]).convert("RGB"))
    cols = (max(0, ox + EDITOR[0]), ox + EDITOR[1])
    try:
        view = newtimeview.view_map(rgb, (oy + BAND[0], oy + BAND[1]), cols, bar_s, approx_s, (oy + WAVE[0], oy + WAVE[1]), peaks,
                                    search_bars=search_bars, min_start_s=min_start_s)
        handle = newtimeview.handle_span(rgb, oy + SCROLL_ROW, (ox + TRACK[0], ox + TRACK[1]))
    except ValueError as e:
        return fail("E_GUI_MISMATCH", "could not read Newtime's view: %s" % e)
    marks = newtimeview.marker_columns(rgb, (oy + WAVE[0], oy + WAVE[1]), cols)
    return ok({"ox": ox, "oy": oy, "cols": cols, "view": view, "handle": handle, "marks": marks})


def _settled(title: str, approx_s: float, bar_s: float, peaks: np.ndarray, min_start_s: float | None) -> Result:
    """Look until two screenshots 0.7 s apart show the same bar lines: FL can still be scrolling from the last clicks (a late arrow click
    moved a whole view 14 px after its markers were placed, 2026-10-29)."""
    seen = _look(title, approx_s, bar_s, peaks, None, min_start_s)
    for _ in range(5):
        if not seen.ok:
            return seen
        time.sleep(0.7)
        again = _look(title, approx_s, bar_s, peaks, None, min_start_s)
        if again.ok and again.value["view"]["bars"] == seen.value["view"]["bars"]:
            return again
        seen = again
    return fail("E_GUI_MISMATCH", "Newtime's view kept moving")


def _page(seen: dict, pages: int) -> None:
    """Page the view right (pages > 0, then STEP_BACK arrow clicks back for overlap) or left by clicking the far end of the scroll track.
    The far end keeps paging the same way however far the handle has moved; at the end it lands on the handle and does nothing. Each
    click is a few px from the last: two clicks on one spot inside the double-click time read as a double-click and did not page."""
    row, ox = seen["oy"] + SCROLL_ROW, seen["ox"]
    end = ox + TRACK[1] - 3 if pages > 0 else ox + TRACK[0] + 2
    for i in range(abs(pages)):
        call("click_at", x=end - (10 * (i % 2) if pages > 0 else -10 * (i % 2)), y=row)
        time.sleep(0.12)
    for i in range(STEP_BACK if pages > 0 else 0):
        call("click_at", x=ox + LEFT_ARROW - 4 + 8 * (i % 2), y=row)
        time.sleep(0.12)


def _to_start(title: str, bar_s: float, peaks: np.ndarray) -> Result:
    """Page left until the scroll handle sits at the start of its track."""
    for _ in range(4):
        seen = _look(title, 0.0, bar_s, peaks, 0)
        if not seen.ok or seen.value["handle"][0] <= seen.value["ox"] + TRACK[0] + 2:
            return seen
        _page(seen.value, -int((seen.value["handle"][0] - seen.value["ox"] - TRACK[0]) // 6) - 3)
    return fail("E_NOT_VERIFIED", "Newtime's view would not page back to the start")


def _click_markers(seen: dict, times: list) -> list:
    v, out = seen["view"], []
    for t in times:
        x = newtimeview.x_for(t, v, seen["cols"][0])
        if all(abs(x - m) > 3 for m in seen["marks"]):
            got = call("click_at", x=int(round(x)), y=seen["oy"] + CLICK_Y, modifiers=["shift"])
            if not got.ok:
                return [got]
            out.append((t, x))
    return out


def add_warp_markers_gui(markers: list[float], duration_s: float, bpm: float, peaks_5ms: list[float] | None = None,
                         title: str = "WarpCorrection") -> Result:
    """Shift+click a warp marker into the open Newtime window at each time (seconds into its sample), scrolling through the sample.

    Needs Newtime at its default size, about 5 s in view, Snap Off. Each view is read from a screenshot, clicked, then checked on a new one.
    Returns placed, verified, missed (clicked, not seen), skipped (never clicked), views, log ([start_s, px_per_s, match, clicked, missed]).
    Errors: E_GUI_MISMATCH (no or resized window, unreadable view), E_NOT_VERIFIED (the view would not scroll), E_HALTED.
    """
    todo = sorted(float(t) for t in markers if 0.0 < float(t) < duration_s)
    peaks, bar_s = np.asarray(peaks_5ms or [], dtype=float), 240.0 / bpm
    first = _to_start(title, bar_s, peaks)
    if not first.ok:
        return first
    placed, missed, skipped, views, approx, prev_lo, prev_h, log = 0, [], [], 0, 0.0, None, None, []
    while todo and views < 600:
        seen = _settled(title, approx, bar_s, peaks, None if prev_lo is None else prev_lo + 0.2)
        if not seen.ok:
            return seen
        v = seen.value["view"]
        lo, hi = v["start_s"], v["start_s"] + (seen.value["cols"][1] - seen.value["cols"][0]) / v["px_per_s"]
        edge = EDGE_PX / v["px_per_s"]
        if v["match"] is not None and v["match"] < 0.4:
            return fail("E_GUI_MISMATCH", "the drawn waveform matches no part of the audio (best %.2f)" % v["match"], placed=placed, log=log)
        if prev_lo is not None and (lo <= prev_lo + 0.05 or seen.value["handle"][0] <= prev_h):
            return fail("E_NOT_VERIFIED", "Newtime's view did not move on from %.2f s" % prev_lo, placed=placed, missed=missed, log=log)
        clicked = _click_markers(seen.value, [t for t in todo if (lo + edge < t or lo < 0.05) and t < hi - edge])
        if clicked and not isinstance(clicked[0], tuple):
            return clicked[0]
        time.sleep(0.3)
        after = _look(title, lo, bar_s, peaks, 0) if clicked else seen
        marks = after.value["marks"] if after.ok else []
        gone = [round(t, 4) for t, x in clicked if all(abs(x - m) > 3.5 for m in marks)]
        if after.ok and clicked and after.value["view"]["bars"] != v["bars"]:
            return fail("E_NOT_VERIFIED", "Newtime's view moved while markers were clicked at %.2f s" % lo, placed=placed + len(clicked), log=log)
        missed, placed, views, prev_lo, prev_h = missed + gone, placed + len(clicked), views + 1, lo, seen.value["handle"][0]
        log.append([round(lo, 3), round(v["px_per_s"], 2), v["match"], len(clicked), len(gone),
                    [round(min((abs(x - m) for m in marks), default=99.0), 1) for t, x in clicked if round(t, 4) in gone]])
        done = {t for t, _ in clicked}
        skipped += [round(t, 4) for t in todo if t not in done and t < hi - edge]
        todo = [t for t in todo if t not in done and t >= hi - edge]
        if todo:
            back = STEP_BACK * LEFT_ARROW / v["px_per_s"]
            pages = max(1, int((todo[0] - edge - lo + back) // (hi - lo)))
            _page(seen.value, pages)
            approx = lo + pages * (hi - lo) - back
    return ok({"placed": placed, "verified": placed - len(missed), "missed": missed, "skipped": skipped + todo, "views": views, "log": log})
