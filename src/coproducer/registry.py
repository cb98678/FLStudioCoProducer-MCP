"""The module registry: load linted modules, validate calls, enforce autonomy, record effects."""
from __future__ import annotations

import contextvars
import importlib.util
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .lint import lint_module
from .manifest import AUTONOMY, LAYERS, load_manifest
from .result import Result, fail
from .schema import normalize_args, validate_args

_CURRENT: contextvars.ContextVar["Registry | None"] = contextvars.ContextVar("coproducer_registry", default=None)
_CALLER: contextvars.ContextVar[tuple[str, ...]] = contextvars.ContextVar("coproducer_callers", default=())

WRITE_CLASSES = ("writes_fl_sandbox",)


@dataclass
class Module:
    name: str
    layer: str
    manifest: dict
    path: Path
    fn: Callable[..., Any] | None
    input_schema: dict
    params: list[str] = field(default_factory=list)

    @property
    def autonomy(self) -> str:
        return self.manifest["policy"]["autonomy"]

    @property
    def side_effect(self) -> str:
        return self.manifest["policy"]["side_effect"]

    @property
    def summary(self) -> str:
        return self.manifest["module"]["summary"]

    @property
    def expose(self) -> bool:
        default = self.layer not in ("L0", "L1")
        return bool(self.manifest["policy"].get("expose", default))


def call_depth() -> int:
    """How many module calls are open in this context (0 means a top-level call)."""
    return len(_CALLER.get())


def call(name: str, /, **kwargs: Any) -> Result:
    """Call a registered module by name through the current registry (the only way modules compose)."""
    reg = _CURRENT.get()
    if reg is None:
        return fail("E_INTERNAL", "no registry is active in this context")
    return reg.call(name, **kwargs)


class Registry:
    def __init__(self, root: Path | str, ceiling: str = "A2",
                 approver: Callable[[str, dict], bool] | None = None,
                 observer: Callable[[str, dict, Result, float], None] | None = None,
                 fl_proxy: Callable[[str, dict], Result] | None = None,
                 enforce_layers: bool = True) -> None:
        self.root = Path(root)
        self.ceiling = ceiling
        self.approver = approver
        self.observer = observer
        self.fl_proxy = fl_proxy
        self.enforce_layers = enforce_layers
        self.modules: dict[str, Module] = {}
        self.rejected: dict[str, list[str]] = {}
        self.halted = False

    # ---------------------------------------------------------------- loading
    def load(self, lint: bool = True, layers: tuple[str, ...] | None = None) -> "Registry":
        dirs = sorted(p.parent for p in self.root.rglob("module.toml"))
        known: dict[str, str] = {}
        for d in dirs:
            try:
                m = load_manifest(d / "module.toml")
                known[m["module"]["name"]] = m["module"]["layer"]
            except Exception:  # noqa: BLE001
                pass
        for d in dirs:
            if lint:
                vs = lint_module(d, known)
                if vs:
                    self.rejected[d.name] = [str(x) for x in vs]
                    continue
            m = load_manifest(d / "module.toml")
            name, layer = m["module"]["name"], m["module"]["layer"]
            if layers and layer not in layers:
                continue
            fn = None
            if layer != "L1":
                fn = self._import(name, d / f"{name}.py")
            schema = json.loads(m["io"]["input"])
            params = list((schema.get("properties") or {}).keys())
            self.modules[name] = Module(name, layer, m, d / f"{name}.py", fn, schema, params)
        return self

    @staticmethod
    def _import(name: str, path: Path) -> Callable[..., Any]:
        modname = f"coproducer_mod_{name}"
        spec = importlib.util.spec_from_file_location(modname, path)
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        sys.modules[modname] = mod
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return getattr(mod, name)

    # ---------------------------------------------------------------- queries
    def names(self, layer: str | None = None) -> list[str]:
        return sorted(n for n, m in self.modules.items() if layer is None or m.layer == layer)

    def exposed(self) -> list[Module]:
        return [m for m in self.modules.values() if m.expose]

    def nearest(self, name: str, n: int = 3) -> list[str]:
        import difflib
        return difflib.get_close_matches(name, list(self.modules), n=n, cutoff=0.5)

    # ---------------------------------------------------------------- calling
    def call(self, name: str, /, **kwargs: Any) -> Result:
        t0 = time.perf_counter()
        res = self._call(name, kwargs)
        if self.observer is not None:
            try:
                self.observer(name, kwargs, res, time.perf_counter() - t0)
            except Exception:  # noqa: BLE001 - an observer must never break a call
                pass
        return res

    def _call(self, name: str, kwargs: dict) -> Result:
        if self.halted:
            return fail("E_HALTED", "registry is halted")
        mod = self.modules.get(name)
        if mod is None:
            return fail("E_NOT_FOUND", f"no module named {name!r}", nearest=self.nearest(name))
        callers = _CALLER.get()
        if self.enforce_layers and callers:
            parent = self.modules.get(callers[-1])
            if parent and LAYERS.index(mod.layer) > LAYERS.index(parent.layer):
                return fail("E_INTERNAL", f"{parent.name} ({parent.layer}) may not call upward to {name} ({mod.layer})")
        lvl = AUTONOMY.index(mod.autonomy)
        if lvl > AUTONOMY.index(self.ceiling):
            return fail("E_AUTONOMY", f"{name} needs {mod.autonomy}; ceiling is {self.ceiling}")
        if mod.autonomy == "A1" and not (self.approver and self.approver(name, kwargs)):
            return fail("E_AUTONOMY", f"{name} is A1 and was not approved")
        chk = validate_args(mod.input_schema, kwargs)
        if not chk.ok:
            return chk
        kwargs = normalize_args(mod.input_schema, kwargs)
        tok_r = _CURRENT.set(self)
        tok_c = _CALLER.set(callers + (name,))
        try:
            if mod.layer == "L1":
                if self.fl_proxy is None:
                    return fail("E_UNSUPPORTED_API", "no FL bridge is attached; L1 ops need one")
                res = self.fl_proxy(name, kwargs)
            else:
                try:
                    res = mod.fn(**kwargs)  # type: ignore[misc]
                except OSError as e:  # a file call the module did not guard (name too long, locked, vanished): the disk said no
                    return fail("E_IO", f"{name}: {type(e).__name__}: {e}"[:300], retryable=False, unguarded=True)
                except Exception as e:  # noqa: BLE001 - modules must not raise; contain it if one does
                    return fail("E_INTERNAL", f"{name} raised {type(e).__name__}: {e}")
        finally:
            _CALLER.reset(tok_c)
            _CURRENT.reset(tok_r)
        if not isinstance(res, Result):
            return fail("E_INTERNAL", f"{name} did not return a Result")
        if res.ok and mod.side_effect in WRITE_CLASSES and mod.layer != "L1" and "verified" not in res.meta:
            return fail("E_NOT_VERIFIED", f"{name} is a write module and did not report meta.verified")
        return res

    def activate(self) -> contextvars.Token:
        """Make this registry the one that `call()` uses in the current context."""
        return _CURRENT.set(self)
