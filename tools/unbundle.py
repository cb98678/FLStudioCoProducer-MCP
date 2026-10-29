"""Split a bundle file into module files.

Sections start with a line `=== <relative path under modules/>`.
A section named `=== @manifest <layer_dir>/<module>` holds `key=value` lines and is expanded to module.toml.
This is an authoring convenience: the output is ordinary files, and the linter judges them.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "modules"


def expand_manifest(path: str, lines: list[str]) -> tuple[str, str]:
    kv: dict[str, str] = {}
    for ln in lines:
        if not ln.strip() or ln.startswith("#"):
            continue
        k, _, v = ln.partition("=")
        kv[k.strip()] = v.strip()
    layer_dir, name = path.split("/")
    layer = kv["layer"]
    calls = [c.strip() for c in kv.get("calls", "").split(",") if c.strip()]
    models = [c.strip() for c in kv.get("models", "").split(",") if c.strip()]
    binaries = [c.strip() for c in kv.get("binaries", "").split(",") if c.strip()]
    packages = [c.strip() for c in kv.get("packages", "").split(",") if c.strip()]
    for s in ("input", "output"):
        json.loads(kv[s])  # fail early on bad JSON
    out = [
        "[module]", f'name = "{name}"', f'layer = "{layer}"',
        f'summary = {json.dumps(kv["summary"])}', f'version = "{kv.get("version", "1.0.0")}"', "",
        "[io]", f"input = '''{kv['input']}'''", f"output = '''{kv['output']}'''", "",
        "[policy]", f'side_effect = "{kv["side"]}"', f'autonomy = "{kv.get("auto", "A0")}"',
        f'cost = "{kv.get("cost", "instant")}"', f'idempotent = {kv.get("idem", "true")}',
        f'verifier = "{kv.get("verifier", "none")}"',
    ]
    if "expose" in kv:
        out.append(f'expose = {kv["expose"]}')
    out += ["", "[deps]", f'min_api = {kv.get("min_api", "0")}', f"calls = {json.dumps(calls)}",
            f"models = {json.dumps(models)}", f"binaries = {json.dumps(binaries)}",
            f"packages = {json.dumps(packages)}", "",
            "[tests]", f'golden = "test_{name}.py::{kv["golden"]}"', f'failure = "test_{name}.py::{kv["failure"]}"']
    if "lines" in kv or "params" in kv or "depth" in kv:
        out += ["", "[budget]"] + [f"{k} = {kv[k]}" for k in ("lines", "params", "depth") if k in kv]
    return f"{layer_dir}/{name}/module.toml", "\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    text = Path(argv[1]).read_text(encoding="utf-8")
    sections: list[tuple[str, list[str]]] = []
    for ln in text.split("\n"):
        if ln.startswith("=== "):
            sections.append((ln[4:].strip(), []))
        elif sections:
            sections[-1][1].append(ln)
    n = 0
    for head, body in sections:
        while body and not body[-1].strip():
            body.pop()
        if head.startswith("@manifest "):
            rel, content = expand_manifest(head.split(None, 1)[1], body)
        else:
            rel, content = head, "\n".join(body) + "\n"
        dest = ROOT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        n += 1
    print(f"wrote {n} files")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
