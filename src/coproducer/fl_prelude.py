"""Helpers shared by every generated FL-side op. Inlined into the dispatcher file.

MUST stay compatible with the Python embedded in FL Studio (about 3.9): no match statements,
no X | Y annotations evaluated at runtime, standard library only.
"""
from __future__ import annotations


def _bad(code, message):
    return {"ok": False, "value": None, "error": {"code": code, "message": message}}


def _check_args(args, kinds):
    """Return an error dict if any argument has the wrong kind, else None.

    Kinds: i int, j int that may be -1 (FL's "none" or "current" for that index), n number, b bool, s str. Names ending in 'index' must
    also be >= 0 (kind i) or >= -1 (kind j).
    """
    for name, kind in kinds.items():
        v = args[name]
        if kind in ("i", "j"):
            good = type(v) is int
        elif kind == "n":
            good = type(v) in (int, float)
        elif kind == "b":
            good = type(v) is bool
        else:
            good = type(v) is str
        if not good:
            return _bad("E_ARG", "%s must be %s" % (name, {"i": "an integer", "j": "an integer", "n": "a number", "b": "a boolean", "s": "a string"}[kind]))
        if kind == "i" and name != "slotIndex" and name.lower().endswith("index") and v < 0:
            return _bad("E_ARG", "%s must be >= 0" % name)
        if kind == "j" and v < -1:
            return _bad("E_ARG", "%s must be >= -1" % name)
    return None


def _run(fn, *a):
    """Call one FL API function and wrap the outcome as {ok, value, error}."""
    try:
        v = fn(*a)
    except (IndexError, ValueError, TypeError, KeyError) as e:
        return _bad("E_ARG", "%s: %s" % (type(e).__name__, e))
    except RuntimeError as e:
        if "range" in str(e).lower():              # FL answers an out-of-range value with RuntimeError("Range error")
            return _bad("E_ARG", "value out of range for FL: %s" % e)
        return _bad("E_INTERNAL", "%s: %s" % (type(e).__name__, e))
    except Exception as e:  # noqa: BLE001
        return _bad("E_INTERNAL", "%s: %s" % (type(e).__name__, e))
    if type(v) is float and (v != v or v in (float("inf"), float("-inf"))):
        v = None if v != v else (999.0 if v > 0 else -999.0)  # JSON has no infinity
    if v is not None and type(v) not in (int, float, bool, str):
        v = str(v)
    return {"ok": True, "value": v, "error": None}


_RAW_ALLOW = set()


def _raw(ns, module, function, args):
    """Call an allowlisted FL function that has no generated op (for example a function newer than the stubs)."""
    key = "%s.%s" % (module, function)
    if key not in _RAW_ALLOW:
        return _bad("E_UNSUPPORTED_API", "%s is not on the raw-call allowlist" % key)
    target = getattr(ns.get(module), function, None)
    if target is None:
        return _bad("E_UNSUPPORTED_API", "%s does not exist in this FL build" % key)
    if type(args) is not list:
        return _bad("E_ARG", "args must be a list")
    return _run(target, *args)
