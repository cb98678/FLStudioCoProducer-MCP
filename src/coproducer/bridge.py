"""Host-side bridge client: one request in, one Result out, built entirely from L0 registry modules."""
from __future__ import annotations

import threading
from typing import Any

from .registry import Registry
from .result import Result, fail, ok
from .services import set_service

MSG_REQUEST, MSG_REPLY, MSG_ERROR, MSG_PING, MSG_PONG = 1, 2, 3, 4, 5
READ_TIMEOUT_S, WRITE_TIMEOUT_S, READ_RETRIES = 2.0, 5.0, 2


class BridgeClient:
    def __init__(self, registry: Registry, transport: Any, max_payload: int = 200, version: int = 1) -> None:
        self.reg, self.transport = registry, transport
        self.max_payload, self.version = max_payload, version
        self._rid = 0
        self._wire = threading.RLock()          # one request on the wire at a time: the transport and the id counter are shared
        set_service("transport", transport)

    def _next_id(self) -> int:
        self._rid = self._rid % 16383 + 1
        return self._rid

    def _frames(self, rid: int, msg_type: int, op: str, args: dict) -> Result:
        call = self.reg.call
        body = call("encode_body", name=op, data=args)
        if not body.ok:
            return body
        packed = call("encode_sysex", data=body.value)
        chunks = call("split_frames", data=packed.value, max_len=self.max_payload)
        frames = []
        for i, chunk in enumerate(chunks.value):
            f = call("build_frame", version=self.version, msg_type=msg_type, req_id=rid, seq=i,
                     total=len(chunks.value), payload=chunk)
            if not f.ok:
                return f
            frames.append(f.value)
        return ok(frames)

    def _once(self, op: str, args: dict, timeout_s: float, msg_type: int) -> Result:
        with self._wire:
            return self._exchange(op, args, timeout_s, msg_type)

    def _exchange(self, op: str, args: dict, timeout_s: float, msg_type: int) -> Result:
        rid = self._next_id()
        frames = self._frames(rid, msg_type, op, args)
        if not frames.ok:
            return frames
        sent = self.reg.call("send_request", frames=frames.value)
        if not sent.ok:
            return sent
        rep = self.reg.call("wait_for_reply", req_id=rid, timeout_s=timeout_s)
        if not rep.ok:
            return rep
        raw = self.reg.call("decode_sysex", data=rep.value["payload"])
        msg = self.reg.call("decode_body", body=raw.value) if raw.ok else raw
        if not msg.ok:
            return msg
        data = msg.value["data"]
        if rep.value["type"] == MSG_PONG:
            return ok(data)
        if data.get("ok"):
            return ok(data.get("value"))
        err = data.get("error") or {}
        return fail(err.get("code", "E_INTERNAL"), err.get("message", "FL reported an error"))

    def request(self, op: str, args: dict | None = None, writes: bool = False, timeout_s: float | None = None) -> Result:
        """Call one FL-side op. Reads retry on timeout; writes never retry."""
        timeout = timeout_s if timeout_s is not None else (WRITE_TIMEOUT_S if writes else READ_TIMEOUT_S)
        tries = 1 if writes else READ_RETRIES + 1
        res = fail("E_INTERNAL", "no attempt made")
        for _ in range(tries):
            res = self._once(op, args or {}, timeout, MSG_REQUEST)
            if res.ok or res.error is None or res.error.code != "E_TIMEOUT":
                return res
        return res

    def ping(self, timeout_s: float = READ_TIMEOUT_S) -> Result:
        return self._once("ping", {}, timeout_s, MSG_PING)

    def fl_proxy(self):
        """Return the callable the Registry uses to run L1 ops through this bridge."""
        def proxy(name: str, kwargs: dict) -> Result:
            mod = self.registry_view.modules.get(name) if hasattr(self, "registry_view") else None
            writes = bool(mod and mod.side_effect == "writes_fl_sandbox")
            return self.request(name, kwargs, writes=writes)
        return proxy

    def attach(self, registry: Registry) -> None:
        """Make `registry` send its L1 calls through this bridge (it may be a different registry than the L0 one)."""
        self.registry_view = registry
        registry.fl_proxy = self.fl_proxy()
