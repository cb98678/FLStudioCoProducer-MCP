from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from coproducer.testrig import desk, ml, procs, rig, run, wav  # noqa: F401,E402  (fixtures)
