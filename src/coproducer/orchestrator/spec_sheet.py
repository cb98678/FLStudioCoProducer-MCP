"""The per-project spec sheet: a markdown file with a small machine-readable header."""
from __future__ import annotations

import re
from pathlib import Path

from ..result import Result, fail, ok

NEEDS = {
    "P0": ("project", "mode"),
    "P1": ("project", "mode", "source"),
    "P2": ("project", "mode", "source", "original_hash"),
    "P3": ("project", "mode", "source", "original_hash", "targets"),
    "P4": ("project", "mode", "source", "original_hash", "targets", "iteration_cap"),
    "P5": ("project", "mode", "source", "original_hash", "targets", "iteration_cap"),
    "P6": ("project", "mode", "source", "original_hash", "targets", "iteration_cap"),
    "P7": ("project", "mode", "source", "original_hash"),
}
MODES = ("new", "restyle", "mix", "master")
_BODY = "# Goals\n\n# Decisions\n\n# Open questions\n\n# Approved by human\n"


def _cast(raw: str):
    raw = re.sub(r"\s+#.*$", "", raw).strip()
    if raw in ("", "null", "none"):
        return None
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    if re.fullmatch(r"-?\d+\.\d+", raw):
        return float(raw)
    return raw


def parse_spec(text: str) -> tuple[dict, str]:
    """Split spec text into (header dict, markdown body)."""
    m = re.match(r"---\n(.*?)\n---\n?(.*)\Z", text, re.S)
    if not m:
        return {}, text
    header = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            k, v = line.split(":", 1)
            header[k.strip()] = _cast(v)
    return header, m.group(2)


def render_spec(header: dict, body: str) -> str:
    lines = ["%s: %s" % (k, "null" if v is None else v) for k, v in header.items()]
    return "---\n" + "\n".join(lines) + "\n---\n" + body


def read_spec(path: Path | str) -> Result:
    p = Path(path)
    if not p.exists():
        return fail("E_NOT_FOUND", "no spec sheet at %s" % p.name)
    header, body = parse_spec(p.read_text(encoding="utf-8"))
    return ok({"header": header, "body": body})


def write_spec(path: Path | str, header: dict, body: str = _BODY) -> Result:
    if header.get("mode") not in MODES:
        return fail("E_ARG", "mode must be one of %s" % ", ".join(MODES))
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render_spec(header, body), encoding="utf-8", newline="\n")
    return ok({"path": str(p)})


def missing_fields(header: dict, phase: str) -> list[str]:
    return [k for k in NEEDS.get(phase, ()) if header.get(k) in (None, "")]


def add_decision(path: Path | str, text: str, reason: str, day: str) -> Result:
    """Add a dated decision with its reason under the Decisions heading."""
    got = read_spec(path)
    if not got.ok:
        return got
    line = "- %s: %s. Reason: %s" % (day, text.rstrip("."), reason)
    body = got.value["body"]
    if "# Decisions" not in body:
        body += "\n# Decisions\n"
    body = re.sub(r"(# Decisions\n)", lambda m: m.group(1) + line + "\n", body, count=1)
    return write_spec(path, got.value["header"], body)


def digest(header: dict, body: str, limit: int = 1500) -> str:
    """A short text the agent reads at the start of each phase."""
    head = "\n".join("%s: %s" % (k, v) for k, v in header.items())
    text = head + "\n\n" + body.strip()
    return text if len(text) <= limit else text[:limit - 3] + "..."
