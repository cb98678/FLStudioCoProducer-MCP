"""The build loop: card to local model to three files to the gate, retrying with the report, then recording every attempt."""
from __future__ import annotations

import json
import time
from pathlib import Path

from .gate import run_gate
from .parse import SYSTEM_PROMPT, build_prompt, card_header, parse_reply, validate_card


def build_card(card_text: str, ask, modules_root: Path, tries: int = 3, gate=run_gate) -> dict:
    """ask(system, user) -> reply text (or raises). Returns {name, passed, attempts: [...], files}. Never writes into modules_root."""
    bad = validate_card(card_text)
    if bad:
        return {"name": None, "passed": False, "attempts": [], "files": {}, "problems": bad}
    name, previous, report, attempts = card_header(card_text)["name"], "", "", []
    for n in range(1, tries + 1):
        began = time.monotonic()
        try:
            reply = ask(SYSTEM_PROMPT, build_prompt(card_text, previous, report))
        except Exception as e:  # noqa: BLE001 - a model server error is a failed attempt, not a crash
            attempts.append({"n": n, "passed": False, "stage": "model", "report": str(e), "secs": round(time.monotonic() - began, 1)})
            continue
        files = parse_reply(reply)
        verdict = gate(name, files, modules_root)
        attempts.append({"n": n, "secs": round(time.monotonic() - began, 1), "chars": len(reply), **verdict})
        if verdict["passed"]:
            return {"name": name, "passed": True, "attempts": attempts, "files": files}
        previous, report = reply, "%s: %s" % (verdict["stage"], verdict["report"])
    return {"name": name, "passed": False, "attempts": attempts, "files": {}}


def save_result(result: dict, out_dir: Path) -> Path:
    """Write the attempt log, and the files when the gate passed, under out_dir/<name>/. A person reviews before registering."""
    d = Path(out_dir) / (result["name"] or "invalid")
    d.mkdir(parents=True, exist_ok=True)
    for f, text in result["files"].items():
        (d / f).write_text(text, encoding="utf-8", newline="\n")
    (d / "attempts.json").write_text(json.dumps(result["attempts"], indent=1), encoding="utf-8", newline="\n")
    return d


def calibration_summary(results: list) -> dict:
    """pass@1, pass@3, mean attempts on passing cards (file 06 section 4)."""
    passed = [r for r in results if r["passed"]]
    first = [r for r in passed if len(r["attempts"]) == 1]
    return {"cards": len(results), "pass_at_1": len(first), "pass_at_3": len(passed),
            "mean_attempts_on_passing": round(sum(len(r["attempts"]) for r in passed) / len(passed), 2) if passed else None}
