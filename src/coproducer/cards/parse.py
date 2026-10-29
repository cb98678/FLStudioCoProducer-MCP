"""Task cards: the one-page work orders given to a local coding model. Parse them, check the eight fields, build the prompt, read the reply."""
from __future__ import annotations

import re

FIELDS = ("Goal", "Signature", "I/O", "Sources", "Imports and class", "Budget", "Acceptance tests", "Out of scope")
LAYER_DIRS = {"L0": "l0_transport", "L1": "l1_fl_ops", "L2": "l2_verified", "L3": "l3_recipes", "L4": "l4_measures", "L5": "l5_models", "L6": "l6_gui"}
SYSTEM_PROMPT = """You write exactly one Python module for a larger system. Follow the card.

Output exactly three files in this order, each in a fenced block labeled with its path:
1. <name>.py       the module. One public function, named as in the card.
2. module.toml     the manifest, filled in from the card.
3. test_<name>.py  pytest tests that implement every acceptance test in the card.

Rules:
- Return a Result using ok(...) or fail(code, message). Never raise.
- Import only what the card allows. Call other modules only with call("name", ...).
- Stay inside the size budget. If you cannot, say so and stop.
- Do not add features the card lists as out of scope.
- Do not write prose outside the three files."""


def card_header(text: str) -> dict:
    """{number, name, layer} from a line like: ### Card 01. `encode_sysex` (L0, pure)."""
    m = re.search(r"^#+ Card (\d+)\.\s+`(\w+)`\s+\((L\d)", text, re.M)
    return {"number": int(m.group(1)), "name": m.group(2), "layer": m.group(3)} if m else {}


def card_fields(text: str) -> dict:
    """Map each numbered bold field name to its text."""
    parts = re.split(r"^(\d)\.\s+\*\*([^*]+?)\.?\*\*\s*", text, flags=re.M)
    out = {}
    for i in range(1, len(parts) - 2, 3):
        out[re.sub(r"\s*\(.*\)$", "", parts[i + 1].strip().rstrip("."))] = parts[i + 2].strip()
    return out


def validate_card(text: str) -> list:
    """Problems that make a card unusable: no header, or a missing or empty field."""
    head, fields = card_header(text), card_fields(text)
    bad = [] if head else ["no header line like: ### Card 01. `name` (L0, pure)"]
    return bad + ["missing field: " + f for f in FIELDS if not fields.get(f)]


def build_prompt(card: str, previous: str = "", report: str = "") -> str:
    """The user message: the card, and on a retry the last output plus the gate report with the one-line instruction."""
    if not previous:
        return card
    return "%s\n\nYour previous output:\n%s\n\nGate report:\n%s\n\nFix only what the report lists." % (card, previous, report)


def parse_reply(reply: str) -> dict:
    """{path: content} from fenced blocks. A block is labeled by its info string (```python name.py) or by the line just before it."""
    files, lines, i = {}, reply.splitlines(), 0
    while i < len(lines):
        m = re.match(r"^```\s*(\S*)\s*(\S*)\s*$", lines[i])
        if not m:
            i += 1
            continue
        label = next((t for t in (m.group(2), m.group(1)) if re.search(r"\.(py|toml)$", t)), "")
        if not label and i > 0:
            prev = re.search(r"([\w./-]+\.(?:py|toml))", lines[i - 1])
            label = prev.group(1) if prev else ""
        j = i + 1
        while j < len(lines) and not lines[j].startswith("```"):
            j += 1
        if label:
            files[label.split("/")[-1]] = "\n".join(lines[i + 1:j]) + "\n"
        i = j + 1
    return files
