from __future__ import annotations

import re

from coproducer import call
from coproducer.result import Result, fail, ok
from coproducer.services import get_service

_KEY = r"^[a-z0-9]$|^f([1-9]|1[0-2])$|^(ctrl|shift|alt|enter|esc|tab|space|home|end|up|down|left|right|backspace|delete|pageup|pagedown)$"
_DENIED = ({"alt", "f4"}, {"ctrl", "alt", "delete"}, {"ctrl", "shift", "esc"})


def press_hotkey(keys: list[str]) -> Result:
    """Press a key chord such as ["ctrl", "shift", "s"] in FL Studio. Window and system keys, Alt+F4 and similar are refused.

    Errors: E_ARG for unknown or denied keys, plus every refusal of check_desktop_ready.
    """
    names = [k.lower() for k in keys]
    if any(not re.match(_KEY, k) for k in names):
        return fail("E_ARG", "unknown key name in %s" % names)
    if any(d <= set(names) for d in _DENIED):
        return fail("E_ARG", "that key chord is not allowed")
    ready = call("check_desktop_ready")
    if not ready.ok:
        return ready
    get_service("desktop").hotkey(names)
    return ok({"pressed": names})
