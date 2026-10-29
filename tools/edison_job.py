"""Write an Edison job: python tools/edison_job.py JOB.json [--out DIR] [--install]

Validates the job (see coproducer.edison.check_job) and writes coproducer_job.json into DIR, the Edison Audio scripts folder
(default: Documents\\Image-Line\\FL Studio\\Settings\\Audio scripts). --install also writes the runner "coproducer run.pyscript".
After running Tools > Scripting > coproducer run in Edison, read coproducer_result.json from the same folder.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from coproducer import edison

DEFAULT = os.path.expanduser(r"~\Documents\Image-Line\FL Studio\Settings\Audio scripts")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("job")
    ap.add_argument("--out", default=DEFAULT)
    ap.add_argument("--install", action="store_true")
    a = ap.parse_args()
    with open(a.job, encoding="utf-8") as f:
        ops = edison.check_job(json.load(f))
    with open(os.path.join(a.out, edison.JOB_FILE), "w", encoding="utf-8") as f:
        json.dump(ops, f)
    if a.install:
        with open(os.path.join(a.out, "coproducer run.pyscript"), "w", encoding="utf-8") as f:
            f.write(edison.runner_script())
    print(f"job with {len(ops)} ops written to {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
