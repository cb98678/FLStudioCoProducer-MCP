"""coproducer: clean-room local AI co-producer for FL Studio."""
from .registry import Registry, call  # noqa: F401
from .result import Error, Result, fail, ok  # noqa: F401

__version__ = "0.1.0"
