"""A stand-in for procs.Procs for tests: FL is open or closed, and every call is logged."""
from __future__ import annotations


class FakeProcs:
    def __init__(self, open_: bool = True, stuck: bool = False) -> None:
        self.open, self.stuck, self.log = open_, stuck, []

    def fl_count(self) -> int:
        return 1 if self.open else 0

    def close_fl(self, timeout_s: float = 30.0) -> bool:
        self.log.append("close")
        if not self.stuck:
            self.open = False
        return not self.open

    def launch(self, exe: str, project: str) -> None:
        self.log.append(("launch", exe, project))
        self.open = True
