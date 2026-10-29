"""Write docs/FILE_MAP.md: one line for every source file, tool, test, doc, skill and data folder, so a new session can find its way.

    python tools/gen_file_map.py            # rewrite docs/FILE_MAP.md
    python tools/gen_file_map.py --check    # exit 1 if the file is out of date (tests/test_file_map.py does the same)

Descriptions come from each file's own docstring (first sentence), so the map cannot drift from the code: change the docstring, rerun this. Folder
descriptions are the DIRS table below and are the only hand-written part.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "FILE_MAP.md"

DIRS = {
    "src/coproducer/": "The library. Every module in `modules/` and every tool in `tools/` imports from here.",
    "src/coproducer/cli/": "The `coproducer` command and its sub-commands (setup, doctor, install-desktop, probe, run, promote ...).",
    "src/coproducer/orchestrator/": "Plans as data, verifiers, the run ledger, phases P0 to P7, human questions and autonomy levels.",
    "src/coproducer/servers/": "The four MCP servers: fl-bridge, studio-audio, studio-ml, desktop-control.",
    "src/coproducer/models/": "GPU budget and scheduler for the local models.",
    "src/coproducer/runners/": "One isolated runner per model (Demucs, Basic Pitch, ACE-Step, Music Flamingo ...).",
    "src/coproducer/cards/": "Task card parsing and the gated build loop that lets a local coding model write new modules.",
    "src/coproducer/data/": "Shipped data: the API inventory, the dependency lock, desktop dialog lists.",
    "modules/": "The tools the agent calls: one folder per module (`module.toml`, one `.py` with one public function, and its test). Layers L0 transport, L1 generated FL ops, L2 verified wrappers, L3 recipes, L4 measures, L5 models, L6 desktop control.",
    "tools/": "Command-line scripts that run on the host: the remix pipeline, measuring, generators, the queue runner. Run with `python tools/NAME.py`.",
    "tests/": "pytest suite for the library and the tools. Module tests live beside each module in `modules/`.",
    "docs/": "Human documentation. Start with `HANDOFF.md`, then `STATUS.md`.",
    "docs/plan/": "The original plan (files 00 to 14) and `15-as-built.md`, which records where the build differs from it.",
    "skills/": "Thirteen skills that teach a local model how to use the system. Each has `SKILL.md`, `evals/prompts.json` and generated catalogs under `references/`.",
    "cards/": "Task cards: work orders for a local coding model.",
    "fl_side/": "The generated controller script that runs inside FL Studio and answers over MIDI SysEx, and the raw-call allow list.",
    "probes/": "Scripts that run inside FL to measure what the API really does (Gate 0).",
    "genre_profiles/": "Genre profiles (templates with FILL blanks; the loaders refuse blanks).",
    "targets/": "Loudness and tonal targets (templates with FILL blanks).",
    "specs/": "Project spec sheets and templates.",
    "recipes/": "Plugin parameter recipes the user approves (nothing shipped).",
    "models/": "`registry.toml`: the model list with sizes and install routes.",
    "runs/": "Run folders (plan, state, ledger, HALT file). Created at run time.",
    "sandbox/": "Host only, not in git: working copies of FL projects, stems, renders, the job queue and deploy folder. See `docs/HANDOFF.md`.",
}

SKIP = {"__init__.py", "__pycache__"}


def _key(p: Path) -> str:
    """Sort by name as plain text: Windows sorts Path objects without regard to case, which would reorder the map between machines."""
    return p.as_posix()


def first_sentence(text: str | None, stops: str = ".:") -> str:
    if not text:
        return "(no docstring)"
    line = " ".join(text.strip().split("\n\n")[0].split()).replace("**", "")
    m = re.match(r"(.+?[%s])(\s|$)" % re.escape(stops), line)
    s = (m.group(1) if m else line).rstrip(":")
    return s if len(s) < 230 else s[:227] + "..."


def py_doc(path: Path) -> str:
    try:
        return first_sentence(ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))))
    except (SyntaxError, UnicodeDecodeError):
        return "(unreadable)"


def md_title(path: Path) -> str:
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    title = next((ln.lstrip("# ").strip() for ln in lines if ln.startswith("#")), path.stem)
    body = next((ln for ln in lines if not ln.startswith("#") and not ln.startswith("|") and not ln.startswith("```") and not ln.startswith("-")), "")
    body = first_sentence(body, ".") if body else ""
    return title if not body or body == "(no docstring)" else f"{title}. {body}"


def skill_desc(path: Path) -> str:
    m = re.search(r"^description:\s*(.+)$", path.read_text(encoding="utf-8"), re.M)
    return first_sentence(m.group(1)) if m else "(no description)"


def table(rows: list[tuple[str, str]]) -> list[str]:
    return ["| File | What it does |", "| --- | --- |"] + [f"| `{a}` | {b.replace('|', '/')} |" for a, b in rows] + [""]


def py_rows(folder: str, pattern: str = "*.py") -> list[tuple[str, str]]:
    return [(f"{folder}{p.name}", py_doc(p)) for p in sorted((ROOT / folder).glob(pattern), key=_key) if p.name not in SKIP]


def test_rows() -> list[tuple[str, str]]:
    rows = []
    for p in sorted((ROOT / "tests").glob("test_*.py"), key=_key):
        doc = ast.get_docstring(ast.parse(p.read_text(encoding="utf-8")))
        rows.append((f"tests/{p.name}", first_sentence(doc) if doc else "Tests for `%s`." % p.stem[5:]))
    rows.append(("tests/conftest.py", "Shared fixtures (`rig`, `wav`, `run`, `desk`) from `coproducer.testrig`."))
    return rows


def build() -> str:
    out = ["# File map", "",
           "Generated by `python tools/gen_file_map.py` from each file's docstring; do not edit by hand (`tests/test_file_map.py` fails when it is stale). "
           "For where to start, read `docs/HANDOFF.md`.", "", "## Folders", ""]
    out += table([(k, v) for k, v in DIRS.items()])
    out += ["## Library: `src/coproducer/`", ""] + table(py_rows("src/coproducer/"))
    for sub in ("cli", "orchestrator", "servers", "models", "runners", "cards"):
        out += [f"### `src/coproducer/{sub}/`", ""] + table(py_rows(f"src/coproducer/{sub}/"))
    out += ["## Tools: `tools/`", ""] + table(py_rows("tools/"))
    out += ["## Tests: `tests/`", ""] + table(test_rows())
    out += ["## FL side", ""] + table(py_rows("fl_side/") + py_rows("probes/"))
    out += ["## Modules: `modules/`", "", "One folder per module. Layer counts and the exposed list come from `coproducer doctor`; every module's own summary is in its `module.toml`.", ""]
    rows = []
    for layer in sorted((p for p in (ROOT / "modules").iterdir() if p.is_dir()), key=_key):
        n = len([d for d in layer.iterdir() if d.is_dir() and (d / "module.toml").is_file()])
        rows.append((f"modules/{layer.name}/", f"{n} modules"))
    out += table(rows)
    out += ["## Skills: `skills/`", ""] + table([(f"skills/{p.parent.name}/SKILL.md", skill_desc(p)) for p in sorted((ROOT / "skills").glob("*/SKILL.md"), key=_key)])
    out += ["## Documents: `docs/`", ""] + table([(f"docs/{p.name}", md_title(p)) for p in sorted((ROOT / "docs").glob("*.md"), key=_key) if p.name != "FILE_MAP.md"])
    out += ["## Plan: `docs/plan/`", ""] + table([(f"docs/plan/{p.name}", md_title(p)) for p in sorted((ROOT / "docs" / "plan").glob("*.md"), key=_key)])
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    text = build()
    if "--check" in sys.argv:
        return 0 if OUT.is_file() and OUT.read_text(encoding="utf-8") == text else 1
    OUT.write_text(text, encoding="utf-8")
    print("wrote", OUT, len(text.splitlines()), "lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
