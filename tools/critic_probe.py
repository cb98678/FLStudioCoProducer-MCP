"""Ask the audio critic (Music Flamingo) several phrasings of one question on clips whose answer is known, to choose the phrasing the panel
uses. Each clip is given as PATH=yes or PATH=no (the known answer); the separation model's vocal and instrumental stems of an excerpt make
good controls.

    python tools/critic_probe.py --clip sandbox\\remix\\x\\master\\panel_excerpt.wav=yes --clip ...\\panel_sep\\..._instrumental.wav=no
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from coproducer import panel  # noqa: E402
from coproducer.servers.common import make_session  # noqa: E402

HOME = Path(__file__).resolve().parents[1]
PROMPTS = [
    ("sung voice", "Is there a sung human voice in this excerpt? Answer yes or no first.", False),
    ("vocals", "Does this clip contain vocals, a person singing or speaking words? Answer yes or no first.", False),
    ("instrumental", "Is this clip purely instrumental, with no human voice at all? Answer yes or no first.", True),
    ("describe", "List every sound source you hear in this clip, including any human voice.", None),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clip", action="append", required=True, help="PATH=yes|no")
    ap.add_argument("--out", default=str(HOME / "sandbox" / "diag" / "critic_probe.json"))
    a = ap.parse_args()
    s = make_session(HOME, "critic_probe", "fl-bridge", "A2")
    rows = []
    for spec in a.clip:
        path, truth = spec.rsplit("=", 1)
        has_voice = truth.lower().startswith("y")
        for name, prompt, inverted in PROMPTS:
            r = s.registry.call("run_model_op", model="flamingo", op="critique", args={"path": path, "prompt": prompt, "max_new_tokens": 80}, timeout_s=900)
            text = r.value["text"] if r.ok else "ERROR %s" % r.error.code
            if inverted is None:
                said = any(w in text.lower() for w in ("voice", "vocal", "sing", "singer", "lyrics", "speech"))
            else:
                yn = panel.yes_no(text)
                said = None if yn is None else (not yn if inverted else yn)
            rows.append({"clip": Path(path).name, "truth": has_voice, "prompt": name, "said_voice": said, "right": said == has_voice, "text": text[:200]})
            print("%-34s truth %-5s %-12s said %-5s %s" % (Path(path).name[:34], has_voice, name, said, text[:90].replace("\n", " ")), flush=True)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(rows, indent=1), encoding="utf-8")
    for name, _, _ in PROMPTS:
        got = [r for r in rows if r["prompt"] == name]
        print("%-12s right %d of %d" % (name, sum(r["right"] for r in got), len(got)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
