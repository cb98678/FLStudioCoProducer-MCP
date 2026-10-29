"""Process-wide service handles (transport, config, sandbox) that modules look up by name.

Services are infrastructure, not modules. A module that needs one declares the
`system` side-effect class. Tests install fakes with `set_service`.
"""
from __future__ import annotations

from typing import Any

_SERVICES: dict[str, Any] = {}


def set_service(name: str, value: Any) -> None:
    _SERVICES[name] = value


def get_service(name: str, default: Any = None) -> Any:
    return _SERVICES.get(name, default)


def clear_services() -> None:
    _SERVICES.clear()
