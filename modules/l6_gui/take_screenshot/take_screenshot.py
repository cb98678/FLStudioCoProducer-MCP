from __future__ import annotations

from pathlib import Path

from coproducer import call
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def take_screenshot(out_path: str) -> Result:
    """Capture FL Studio's window to a PNG inside the sandbox folder. Coordinates in the image match click_at coordinates."""
    root = get_service("sandbox_root")
    chk = call("check_sandbox_path", path=out_path, sandbox_root=str(root)) if root else fail("E_SANDBOX_VIOLATION", "no sandbox folder")
    ready = call("check_desktop_ready") if chk.ok else chk
    if not ready.ok:
        return ready
    w = ready.value
    desk = get_service("desktop")
    shot = desk.grab((w["left"], w["top"], w["left"] + w["width"], w["top"] + w["height"]))
    Path(chk.value["resolved"]).parent.mkdir(parents=True, exist_ok=True)
    desk.save_png(shot, chk.value["resolved"])
    return ok({"path": chk.value["resolved"], "width": w["width"], "height": w["height"]})
