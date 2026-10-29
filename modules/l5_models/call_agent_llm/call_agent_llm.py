from __future__ import annotations

import json
import urllib.error
import urllib.request

from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def call_agent_llm(prompt: str, system: str = "", tools: list | None = None, temperature: float = 0.2, max_tokens: int = 1024) -> Result:
    """Send one chat turn to the local OpenAI-compatible endpoint and return the reply message and any tool calls.

    The endpoint and model come from config.toml [llm]. Errors: E_UNSUPPORTED_API when unset, E_MODEL when it cannot be reached.
    """
    cfg = get_service("llm")
    if not cfg or not cfg.get("endpoint"):
        return fail("E_UNSUPPORTED_API", "no [llm] endpoint is configured")
    messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
    body = {"model": cfg.get("model", ""), "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    if tools:
        body["tools"] = tools
    req = urllib.request.Request(cfg["endpoint"].rstrip("/") + "/chat/completions", data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=cfg.get("timeout_s", 120)) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        choice = data["choices"][0]
    except (urllib.error.URLError, OSError, ValueError, KeyError, IndexError) as e:
        return fail("E_MODEL", "cannot get a reply from the local LLM: %s" % e, retryable=True)
    return ok({"message": choice["message"], "finish_reason": choice.get("finish_reason"), "usage": data.get("usage", {})})
