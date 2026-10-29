from __future__ import annotations

from coproducer import call
from coproducer.result import Result


def set_sidechain_source_gui(dest: int, position: int = 1) -> Result:
    """In the open Fruity Limiter window of mixer track dest, choose the position-th sidechain source (1 is the first, in track order).

    The plugin exposes no sidechain parameter, so this cannot be read back through the API. Runs the recipe set_limiter_sidechain_gui.
    Errors: E_GUI_MISMATCH when no Fruity Limiter window is open on that track, E_HALTED.
    """
    return call("run_gui_recipe", name="set_limiter_sidechain_gui", params={"dest": dest, "position": position})
