"""Section-aware drum plan for sampler-channel patterns: grooves, breaks, snare-roll builds, drops, fills, crashes, FX cues.

Input is a list of sections {"name", "start", "end"} in bars (end exclusive) using the names intro, kickin, groove,
break, build, drop, main, dip, outro. Output is plain event tuples (bar, step, inst, vel 0..1, pan -1..1, key) on the
16-step grid, so the plan can be reviewed as data before anything is written into a project.
"""
from __future__ import annotations

from .flpfile import TICKS_PER_BAR, note_bytes

STEP_TICKS = TICKS_PER_BAR // 16
SECTION_NAMES = ("intro", "kickin", "groove", "break", "build", "drop", "main", "dip", "outro")
ROLL_DIVISIONS = (4, 2, 1, 0.5)  # steps between hits: quarter, eighth, sixteenth, thirty-second
Event = tuple[int, float, str, float, float, int]


class Plan:
    def __init__(self) -> None:
        self.events: list[Event] = []
        self.labels: dict[int, str] = {}

    def ev(self, bar: int, step: float, inst: str, vel: float, pan: float = 0.0, key: int = 60) -> None:
        self.events.append((bar, float(step), inst, float(vel), float(pan), int(key)))

    def kick(self, bar: int, step: int, gain: float = 1.0, hi: bool = False) -> None:
        self.ev(bar, step, "kick", gain * 0.95, 0, 64 if hi else 60)

    def kick4(self, bar: int, gain: float = 1.0, hi: bool = False) -> None:
        for s in (0, 4, 8, 12):
            self.kick(bar, s, gain, hi)

    def backbeat(self, bar: int, gain: float = 1.0, clap_on: bool = True) -> None:
        for s in (4, 12):
            self.ev(bar, s, "snare", 0.62 * gain * 1.1)
            if clap_on:
                self.ev(bar, s, "clap", 0.75 * gain)

    def roll(self, bar: int, start: float, end: float, sub: float, v0: float, v1: float) -> None:
        n = len(range(int(start / sub), int(end / sub)))
        for k in range(n):
            self.ev(bar, start + k * sub, "snare", (v0 + (v1 - v0) * k / max(n - 1, 1)) * 0.9, 0.06 * (-1) ** k, 60 + round(4 * k / max(n - 1, 1)))

    def hats(self, bar: int, mode: str, vel: float = 1.0) -> None:
        for s in range(16):
            pan = 0.14 * (1 if (s // 2) % 2 else -1)
            if mode in ("full", "e8") and s % 4 == 0:
                self.ev(bar, s, "hat", 0.90 * vel, pan)
            if mode in ("full", "off") and s % 4 == 2:
                self.ev(bar, s, "ohat", 0.75 * vel, pan)
            if mode == "e8" and s % 4 == 2:
                self.ev(bar, s, "hat", 0.60 * vel, pan)
            if mode == "full" and s % 2 == 1:
                self.ev(bar, s, "hat", (0.30 + 0.045 * ((s * 7) % 5)) * vel, -pan)
            if mode == "sparse" and s % 4 == 2:
                self.ev(bar, s, "hat", 0.66 * vel, pan)

    def shaker(self, bar: int, vel: float = 1.0) -> None:
        for s in range(16):
            self.ev(bar, s, "shaker", (0.90 if s % 4 == 0 else 0.54 if s % 2 == 0 else 0.36) * vel, 0.2 * (1 if s % 2 else -1))

    def groove(self, bar: int, hat_mode: str = "full", shake: bool = False) -> None:
        self.kick4(bar)
        self.backbeat(bar)
        self.hats(bar, hat_mode)
        if shake:
            self.shaker(bar)

    def fill(self, bar: int, kind: str) -> None:
        if kind in ("A", "D"):
            long = kind == "D"
            self.roll(bar, 8, 16, 2, 0.3 if long else 0.35, 0.6 if long else 0.7)
            self.roll(bar, 12, 16, 1, 0.5, 0.95 if long else 1.0)
        elif kind == "B":
            for k, (s, i) in enumerate(((8, 0), (9.5, 0), (10, 1), (11, 1), (12, 2), (13, 2), (14, 3), (15, 3))):
                self.ev(bar, s, "tom", 0.8, -0.2 + 0.12 * k, (67, 64, 60, 55)[i])
            for s in (12, 14, 15):
                self.kick(bar, s, 0.9)
        elif kind == "C":
            for k in range(8):
                self.ev(bar, 8 + k, "hat", (0.18 + 0.3 * k / 8) * 3.0, 0.1 * (-1) ** k)
            for s in (12, 13, 14, 15):
                self.ev(bar, s, "clap", 0.5 + 0.12 * (s - 12))
            self.ev(bar, 15.5, "ohat", 1.0)


def _section(plan: Plan, name: str, b: int, a: int, z: int) -> None:
    k, n = b - a, z - a
    if name == "intro":
        plan.hats(b, "e8", 0.5 + 0.12 * k)
        plan.shaker(b, 0.6 + 0.1 * k)
        if k == n - 1:
            plan.roll(b, 12, 16, 1, 0.2, 0.5)
    elif name == "kickin":
        plan.kick4(b)
        plan.hats(b, "full", 0.8)
        plan.shaker(b, 0.7)
        if k >= n // 2:
            plan.backbeat(b)
        else:
            for s in (4, 12):
                plan.ev(b, s, "rim", 0.6)
    elif name in ("groove", "main"):
        plan.groove(b, "full", shake=(name == "main" or k >= 8))
        if name == "groove" and k in (4, 12):
            plan.ev(b, 14, "tom", 0.6, 0, 64)
            plan.ev(b, 15, "tom", 0.6, 0, 60)
        if name == "main" and b % 4 == 3:
            for s, key in ((14, 64), (14.5, 60), (15, 55)):
                plan.ev(b, s, "tom", 0.55, 0, key)
    elif name == "break":
        plan.hats(b, "e8", 0.45 + 0.08 * k)
        for s in (4, 12):
            plan.ev(b, s, "rim", 0.55)
        if k == n - 1:
            for s in (0, 4, 8, 12):
                plan.ev(b, s + 2, "rim", 0.35)
    elif name == "build":
        p = k / n
        if p < 0.5:
            plan.kick4(b, 0.7 + 0.1 * k, hi=True)
        elif p < 0.75:
            for s in range(0, 16, 2):
                plan.kick(b, s, 0.75, hi=True)
        plan.hats(b, "full" if p >= 0.5 else "e8", 0.6 + 0.15 * k)
        div = ROLL_DIVISIONS[min(3, int(p * 4))]
        last = k == n - 1
        plan.roll(b, 0, 14 if last else 16, div, 0.35 + 0.35 * p if not last else 0.7, 0.55 + 0.35 * p if not last else 1.0)
    elif name == "drop":
        plan.kick4(b)
        plan.backbeat(b)
        plan.hats(b, "off", 0.9)
        if b % 2 == 1:
            plan.ev(b, 10, "rim", 0.5)
    elif name == "dip":
        plan.hats(b, "sparse", 0.7)
        plan.ev(b, 12, "rim", 0.6)
        plan.roll(b, 12, 16, 1, 0.3, 0.9)
    elif name == "outro":
        g = 1.0 - 0.35 * k if k < n - 1 or n == 1 else 0.8
        if k == n - 1 and n > 1 and z - a >= 3:
            plan.kick(b, 0, 0.8)
        else:
            plan.kick4(b, g)
            plan.hats(b, "off", 0.8 * g)
            if k == 0:
                plan.backbeat(b, 0.8)


def plan_drums(sections: list[dict], fills: dict[int, str] | None = None, crashes: dict[int, float] | None = None) -> Plan:
    """Build the event list. fills maps bar to a fill kind A (snare roll), B (toms), C (hat and clap) or D (long roll)."""
    plan = Plan()
    for s in sections:
        if s["name"] not in SECTION_NAMES:
            raise ValueError("unknown section name %r" % s["name"])
        for b in range(s["start"], s["end"]):
            plan.labels[b] = s["name"]
            _section(plan, s["name"], b, s["start"], s["end"])
    for b, kind in (fills or {}).items():
        plan.fill(b, kind)
        plan.labels[b] = plan.labels.get(b, "") + "+fill"
    for b, g in (crashes or {}).items():
        plan.ev(b, 0, "crash", g, 0.15 if b % 8 else -0.15)
    return plan


def default_crashes(sections: list[dict]) -> dict[int, float]:
    """Crash on every section start after the first, louder on drop and main, plus every 4th bar inside long sections."""
    out: dict[int, float] = {}
    for s in sections[1:]:
        if s["name"] != "build" and s["name"] != "dip":
            out[s["start"]] = 0.75 if s["name"] in ("drop", "main") else 0.55
        if s["name"] in ("drop", "main", "groove"):
            for b in range(s["start"] + 4, s["end"], 4):
                out[b] = 0.55
    return out


def fx_cues(sections: list[dict]) -> list[dict]:
    """Audio FX that do not belong in a sampler: impacts on drops, reverse crashes into section starts, noise and tone risers over breaks and builds, downlifters after drops."""
    cues: list[dict] = []
    for i, s in enumerate(sections):
        n = s["end"] - s["start"]
        if i and s["name"] in ("drop", "main", "groove", "kickin"):
            cues.append({"kind": "impact", "bar": s["start"], "gain": 1.0 if s["name"] == "drop" else 0.45})
            cues.append({"kind": "reverse_crash", "bar": s["start"], "beats": 8 if s["name"] == "drop" else 4, "gain": 0.7 if s["name"] == "drop" else 0.4})
        if s["name"] == "break":
            cues.append({"kind": "noise_riser", "bar": s["start"], "bars": n, "f0": 350, "f1": 14000, "gain": 0.5})
        if s["name"] == "build":
            cues.append({"kind": "noise_riser", "bar": s["start"], "bars": n, "f0": 500, "f1": 16000, "gain": 0.45})
            cues.append({"kind": "tone_riser", "bar": s["start"], "bars": n, "f0": 174.6, "f1": 1396.9, "gain": 0.22})
        if s["name"] == "drop":
            cues.append({"kind": "downlifter", "bar": s["start"], "beats": 4, "gain": 0.35})
    return cues


def to_note_bytes(plan: Plan, channels: dict[str, int]) -> dict[int, bytes]:
    """Per-bar pattern bytes for the plan. channels maps inst name to the sampler channel id; unknown inst names raise KeyError."""
    rows: dict[int, list[tuple[int, int, bytes]]] = {}
    for bar, step, inst, vel, pan, key in plan.events:
        pos = int(round(step * STEP_TICKS))
        v = max(1, min(127, int(round(min(vel, 1.0) * 127))))
        p = max(0, min(128, int(round(64 + pan * 63))))
        rows.setdefault(bar, []).append((pos, channels[inst], note_bytes(pos, channels[inst], key, 0, v, p)))
    return {b: b"".join(r[2] for r in sorted(v, key=lambda r: (r[0], r[1]))) for b, v in rows.items()}

