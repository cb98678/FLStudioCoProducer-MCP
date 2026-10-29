"""Run the generated FL-side file under Python 3.9 (the oldest interpreter FL may embed), when available."""
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def _py39():
    for cand in ("python3.9", str(Path.home() / ".local/share/uv/python/cpython-3.9.25-linux-x86_64-gnu/bin/python3.9")):
        p = shutil.which(cand) or (cand if Path(cand).exists() else None)
        if p:
            return p
    return None


@pytest.mark.skipif(_py39() is None, reason="python3.9 not installed")
def test_script_runs_on_python39():
    out = subprocess.run([_py39(), "-I", str(REPO / "tools" / "smoke_fl39.py")], capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    assert "OK 3.9" in out.stdout
