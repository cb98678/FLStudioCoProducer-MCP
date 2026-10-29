from __future__ import annotations

import json
from pathlib import Path

from coproducer import call
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def _allowed() -> list:
    folder = get_service("recipes_dir")
    try:
        return json.loads((Path(folder) / "_dialogs.json").read_text(encoding="utf-8")).get("allow", [])
    except (OSError, TypeError, ValueError):
        return []


def _rule(title: str, allow: list):
    return next((a for a in allow if a["contains"].lower() in title.lower()), None)


def dismiss_dialog_gui() -> Result:
    """Close the topmost open dialog only when its title is on the human-confirmed allow list (_dialogs.json).

    An unknown dialog sets the halt flag and fails with E_BLOCKED_BY_DIALOG so a person looks at it. Returns dismissed false when no dialog is open.
    """
    found = call("list_open_dialogs")
    if not found.ok or not found.value["dialogs"]:
        return found if not found.ok else ok({"dismissed": False})
    title = found.value["dialogs"][0]["title"]
    rule = _rule(title, _allowed())
    if rule is None:
        call("halt_input")
        return fail("E_BLOCKED_BY_DIALOG", "an unknown dialog is open and was left alone: %r" % title, title=title)
    pressed = call("press_hotkey", keys=[rule["key"]])
    return pressed if not pressed.ok else ok({"dismissed": True, "title": title, "key": rule["key"]})
