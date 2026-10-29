from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def get_fl_versions() -> Result:
    """Return the FL version and API level recorded by the last Gate 0 probe, from configuration.

    Errors: E_NOT_FOUND when no probe has been recorded.
    """
    fl = call("get_config_value", key="probe.fl_version")
    api = call("get_config_value", key="probe.api_level")
    if not (fl.ok and api.ok):
        return fail("E_NOT_FOUND", "no probe result is recorded; run the Gate 0 probes")
    return ok({"fl": fl.value, "api": api.value})
