"""Ask a local Ollama server to drop a model from memory. One function, standard library only.

Docs checked 2026-10-18: https://docs.ollama.com/faq (POST /api/generate with keep_alive 0 unloads the model right away).
The model loads again on its own at the next chat request.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request


def native_base(endpoint: str) -> str:
    """The server root for an OpenAI style endpoint such as http://127.0.0.1:11434/v1 ."""
    base = endpoint.rstrip("/")
    return base[:-3] if base.endswith("/v1") else base


def unload(endpoint: str, model: str, timeout_s: float = 10.0) -> bool:
    """True when the server accepted the unload request. False when it is unreachable or no model is named."""
    if not endpoint or not model:
        return False
    req = urllib.request.Request(native_base(endpoint) + "/api/generate", data=json.dumps({"model": model, "keep_alive": 0}).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            resp.read()
        return True
    except (urllib.error.URLError, OSError, ValueError):
        return False
