"""Shared fixtures for module tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from coproducer.registry import Registry
from coproducer.services import clear_services
from coproducer.testrig import desk, ml, procs, rig, run, wav  # noqa: F401  (fixtures shared with module tests)

ROOT = Path(__file__).resolve().parent


def find_module_file(name: str) -> Path:
    hits = list(ROOT.rglob(f"{name}/{name}.py"))
    if not hits:
        raise FileNotFoundError(name)
    return hits[0]


@pytest.fixture(scope="session")
def fn():
    """Return a loader: fn("encode_sysex") gives the module's function, imported by path."""
    def load(name: str):
        return Registry._import(name, find_module_file(name))
    return load


@pytest.fixture(autouse=True)
def _clean_services():
    clear_services()
    yield
    clear_services()
