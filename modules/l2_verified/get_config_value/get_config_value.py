from __future__ import annotations

from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def get_config_value(key: str) -> Result:
    """Return one value from the loaded configuration by dotted key, such as sandbox.root.

    Errors: E_NOT_FOUND when the key is absent or no configuration is loaded.
    """
    node = get_service("config")
    if not isinstance(node, dict):
        return fail("E_NOT_FOUND", "no configuration is loaded")
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            return fail("E_NOT_FOUND", "config has no key %r" % key)
        node = node[part]
    return ok(node)
