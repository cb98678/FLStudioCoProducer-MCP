"""Collaboration with the human: questions with options, approvals, and the pending-decisions file."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from ..result import Result, fail, ok


class ScriptedCollab:
    """Answers from a fixed list. For tests and for runs where the answers are known ahead of time."""

    def __init__(self, answers: list | None = None, approve_all: bool = False) -> None:
        self.answers = list(answers or [])
        self.approve_all = approve_all
        self.asked: list[dict] = []

    def ask(self, question: str, options: list[str]) -> Result:
        self.asked.append({"question": question, "options": options})
        if not self.answers:
            return fail("E_PENDING_HUMAN", "no scripted answer left", question=question)
        return ok({"choice": self.answers.pop(0), "note": ""})

    def approve(self, what: str, detail: dict) -> Result:
        self.asked.append({"approve": what})
        return ok(True) if self.approve_all else fail("E_PENDING_HUMAN", "approval needed: %s" % what, what=what)


class PendingCollab:
    """Unattended mode: never guesses. Writes the question to a file and reports E_PENDING_HUMAN."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def _add(self, item: dict) -> None:
        items = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else []
        if item not in items:
            items.append(item)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(items, indent=2), encoding="utf-8", newline="\n")

    def ask(self, question: str, options: list[str]) -> Result:
        self._add({"question": question, "options": options})
        return fail("E_PENDING_HUMAN", "waiting for a human answer", question=question)

    def approve(self, what: str, detail: dict) -> Result:
        self._add({"approve": what, "detail": detail})
        return fail("E_PENDING_HUMAN", "waiting for approval: %s" % what, what=what)


class CallbackCollab:
    """Delegates to two functions, for example a terminal prompt or a GUI dialog."""

    def __init__(self, ask_fn: Callable[[str, list], str], approve_fn: Callable[[str, dict], bool]) -> None:
        self.ask_fn, self.approve_fn = ask_fn, approve_fn

    def ask(self, question: str, options: list[str]) -> Result:
        return ok({"choice": self.ask_fn(question, options), "note": ""})

    def approve(self, what: str, detail: dict) -> Result:
        return ok(True) if self.approve_fn(what, detail) else fail("E_PENDING_HUMAN", "approval declined: %s" % what, what=what)
