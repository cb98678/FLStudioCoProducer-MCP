"""Put remixes side by side: what the variety engine chose for each and what came out (form, groove, kit, parts, sounds, loudness).

    python tools/compare_remixes.py sandbox\\remix\\curse_house_varA sandbox\\remix\\curse_house_varB [--out sandbox\\remix\\compare.md]

Each folder is a tools/remix_song.py work folder (plan.json and remix_report.json). Prints a Markdown table, one column per remix, and
how many categories differ between each pair, so a repeated format shows up before anyone listens.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from coproducer import variety  # noqa: E402

ROWS = ("form", "drums", "kit", "bass", "chords", "arp", "harmony", "fx", "mix", "vocal", "automation")


def load(folder: Path) -> dict:
    """The plan and the report of one work folder ({} for what is missing)."""
    read = lambda p: json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}  # noqa: E731
    return {"name": folder.name, "plan": read(folder / "plan.json"), "report": read(folder / "remix_report.json")}


def shape(plan: dict) -> str:
    """The arrangement in one line: section name and bars."""
    return " ".join("%s %d" % (s["name"], s["end"] - s["start"]) for s in plan.get("sections", [])) or "-"


def master(report: dict) -> str:
    """The club master's measured loudness and true peak, from the report's master step."""
    step = next((s for s in report.get("steps", []) if s.get("step") == "master" and s.get("ok")), {})
    got = (step.get("value") or {}).get("measured") or {}
    if not isinstance(got.get("lufs"), (int, float)):
        return "-"
    return "%.1f LUFS, %.1f dBTP" % (got["lufs"], got.get("true_peak_dbtp", float("nan")))


def label(bank: dict, oid: str | None) -> str:
    """An option's label (its id when the bank no longer has it)."""
    if not oid:
        return "the pack as written"
    try:
        return variety.find(bank, oid)["label"]
    except variety.VarietyError:
        return oid


def table(rows: list[dict], bank: dict) -> list[str]:
    out = ["| | " + " | ".join(r["name"] for r in rows) + " |", "| --- |" + " --- |" * len(rows)]
    out.append("| style, bpm | " + " | ".join("%s, %s" % (r["plan"].get("style", "-"), r["plan"].get("bpm", "-")) for r in rows) + " |")
    out.append("| sections | " + " | ".join(shape(r["plan"]) for r in rows) + " |")
    for cat in ROWS:
        out.append("| %s | " % cat + " | ".join(label(bank, ((r["plan"].get("variety") or {}).get("choices") or {}).get(cat)) for r in rows) + " |")
    snd = lambda r: ", ".join("%s: %s" % (k, label(bank, v)) for k, v in ((r["plan"].get("variety") or {}).get("sounds") or {}).items()) or "-"  # noqa: E731
    out.append("| sounds | " + " | ".join(snd(r) for r in rows) + " |")
    out.append("| surprise | " + " | ".join(((r["plan"].get("variety") or {}).get("surprise") or {}).get("id", "-") for r in rows) + " |")
    out.append("| master | " + " | ".join(master(r["report"]) for r in rows) + " |")
    return out


def differences(rows: list[dict]) -> list[str]:
    """How many of the categories differ between each pair of remixes."""
    out = []
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            ca, cb = ((a["plan"].get("variety") or {}).get("choices") or {}), ((b["plan"].get("variety") or {}).get("choices") or {})
            if not ca or not cb:   # a remix from before the variety engine (or with it off) has no choices to compare
                out.append("- %s and %s: %s has no variety record, compare by ear" % (a["name"], b["name"], a["name"] if not ca else b["name"]))
                continue
            n = sum(ca.get(c) != cb.get(c) for c in ROWS)
            out.append("- %s and %s differ in %d of %d categories%s" % (a["name"], b["name"], n, len(ROWS),
                                                                        "" if shape(a["plan"]) == shape(b["plan"]) else ", and in their sections"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folders", nargs="+")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    rows = [load(Path(f)) for f in a.folders]
    text = "\n".join(table(rows, variety.load_bank()) + [""] + differences(rows)) + "\n"
    print(text)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
