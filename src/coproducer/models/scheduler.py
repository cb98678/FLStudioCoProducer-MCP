"""GPU scheduler: load and unload model workers so memory never runs out, and say what it did."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from ..result import Result, fail, ok
from .spec import ModelSpec


@dataclass
class Resident:
    spec: ModelSpec
    worker: Any
    variant: str
    need_mb: int
    last_used: int = 0


@dataclass
class Scheduler:
    registry: dict[str, ModelSpec]
    make_worker: Callable[[ModelSpec], Any]
    query_vram: Callable[[], tuple[int, int] | None]
    ledger: Any = None
    phase_hints: dict = field(default_factory=lambda: {"P1": ("demucs", "basicpitch"), "P3": ("acestep",), "P5": ("flamingo",)})
    resident: dict = field(default_factory=dict)
    clock: int = 0
    phase: str = "P0"
    budget_mb: int | None = None             # optional cap below the card's real size, for headroom
    release_external: Callable[[], bool] | None = None   # frees memory held by something we do not run, such as the Ollama brain
    settle_s: float = 0.5                    # how long to wait between memory checks after a release

    def _log(self, kind: str, **fields: Any) -> None:
        if self.ledger is not None:
            self.ledger.append(kind, **fields)

    def free_mb(self) -> int | None:
        got = self.query_vram()
        if got is None:
            return None
        free = got[0]
        return min(free, self.budget_mb - sum(r.need_mb for r in self.resident.values())) if self.budget_mb else free

    def _evict_order(self) -> list[str]:
        wanted = self.phase_hints.get(self.phase, ())
        return sorted(self.resident, key=lambda n: (n in wanted, self.resident[n].last_used))

    def _make_room(self, need: int) -> bool:
        for name in self._evict_order():
            free = self.free_mb()
            if free is None or free >= need:
                return True
            self.unload(name)
        free = self.free_mb()
        if (free is None or free >= need) or self.release_external is None:
            return free is None or free >= need
        if self.release_external():
            for _ in range(8):
                free = self.free_mb()
                if free is None or free >= need:
                    self._log("external_release", free_after_mb=free)
                    return True
                time.sleep(self.settle_s)
        return False

    def _pick_variant(self, spec: ModelSpec, variant: str | None) -> str:
        return variant or spec.default_variant or (spec.variants[0] if spec.variants else "")

    def load(self, name: str, variant: str | None = None) -> Result:
        """Make sure a model's worker is running. Evicts the least useful resident model if memory is short."""
        spec = self.registry.get(name)
        if spec is None:
            return fail("E_NOT_FOUND", "no model named %r" % name, nearest=sorted(self.registry)[:5])
        self.clock += 1
        use = self._pick_variant(spec, variant)
        held = self.resident.get(name)
        if held and held.variant == use and held.worker.alive():
            held.last_used = self.clock
            return ok({"model": name, "variant": use, "already_loaded": True})
        if held:
            self.unload(name)
        if spec.vram_typical_mb and not self._make_room(spec.vram_typical_mb):
            return fail("E_GPU_BUDGET", "%s needs about %d MB and it will not fit" % (name, spec.vram_typical_mb),
                        need_mb=spec.vram_typical_mb, free_mb=self.free_mb(), resident=sorted(self.resident))
        return self._start(spec, use)

    def _start(self, spec: ModelSpec, variant: str) -> Result:
        worker = self.make_worker(spec)
        started = worker.start()
        if not started.ok:
            return started
        init = worker.call("load", {"model": spec.name, "variant": variant}, timeout_s=900)
        if not init.ok:
            worker.stop()
            return init
        self.resident[spec.name] = Resident(spec, worker, variant, spec.vram_typical_mb, self.clock)
        self._log("model_load", model=spec.name, variant=variant, free_after_mb=self.free_mb())
        return ok({"model": spec.name, "variant": variant, "already_loaded": False})

    def unload(self, name: str) -> Result:
        held = self.resident.pop(name, None)
        if held is None:
            return ok({"model": name, "was_loaded": False})
        held.worker.call("unload", {}, timeout_s=30)
        held.worker.stop()
        self._log("model_unload", model=name)
        return ok({"model": name, "was_loaded": True})

    def run_op(self, name: str, op: str, args: dict, timeout_s: float = 600.0) -> Result:
        """Load the model if needed, then run one op on its worker."""
        loaded = self.load(name)
        if not loaded.ok:
            return loaded
        self.clock += 1
        self.resident[name].last_used = self.clock
        return self.resident[name].worker.call(op, args, timeout_s)

    def unload_all(self) -> None:
        for name in list(self.resident):
            self.unload(name)

    def status(self) -> dict:
        got = self.query_vram()
        return {"free_mb": got[0] if got else None, "total_mb": got[1] if got else None,
                "resident": {n: {"variant": r.variant, "need_mb": r.need_mb} for n, r in self.resident.items()}}
