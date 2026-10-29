"""docs/FILE_MAP.md is generated from docstrings and must not drift."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _tool():
    spec = importlib.util.spec_from_file_location("gen_file_map", ROOT / "tools" / "gen_file_map.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_file_map_is_current():
    text = _tool().build()
    assert (ROOT / "docs" / "FILE_MAP.md").read_text(encoding="utf-8") == text, "run: python tools/gen_file_map.py"


def test_file_map_has_no_undocumented_library_file():
    text = _tool().build()
    assert "(no docstring)" not in text.split("## Tools")[0], "a library file lacks a docstring"
    assert "—" not in text
