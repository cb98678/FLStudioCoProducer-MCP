from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail

DB_PER_UNIT = 31.0


def set_eq_db_verified(index: int, band: int, db: float) -> Result:
    """Set a built-in mixer EQ band (0 low shelf, 1 mid peak, 2 high shelf) to a gain in dB, within plus or minus 15 dB.

    Uses the measured scale of 31 dB per raw unit (0.5 is flat). Errors: E_ARG for a bad band or range.
    """
    if band not in (0, 1, 2) or not -15.0 <= db <= 15.0:
        return fail("E_ARG", "band must be 0, 1 or 2 and db within plus or minus 15")
    return call("set_eq_gain_verified", index=index, band=band, value=round(0.5 + db / DB_PER_UNIT, 4))
