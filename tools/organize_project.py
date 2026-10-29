"""Apply the house project standard (docs/PROJECT_STANDARD.md) to a copy of a project. Run from the repo root:
python tools/organize_project.py SOURCE.flp OUT.flp [--dry-run] [--drop-unused]
OUT must sit under a folder named sandbox. The source is only read."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, "src")
from coproducer import flpfile, projorg  # noqa: E402


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 2 or "sandbox" not in [p.lower() for p in os.path.abspath(args[1]).split(os.sep)]:
        print("usage: organize_project.py SOURCE.flp OUT.flp (OUT under a sandbox folder) [--dry-run]")
        return 2
    f = flpfile.Flp.load(args[0])
    plan = projorg.plan(f)
    if "--dry-run" in argv:
        print(json.dumps(plan, indent=1, default=list))
        return 0
    unused = projorg.unused_channels(f)
    dropped = projorg.drop_unused(f) if "--drop-unused" in argv else []
    plan = projorg.plan(f)
    counts = projorg.apply(f, plan)
    f.save(args[1])
    left = projorg.check(flpfile.Flp.load(args[1]))
    print("wrote", args[1], counts)
    print("silent channels (no notes, no clips):", [(u["name"], "insert %s" % u["track"]) for u in unused])
    print("removed (silent and routed to no insert):", [u["name"] for u in dropped])
    print("unclassified channels:", [r["old"] for r in plan["channels"] if not r["family"]])
    print("left to fix:", left or "none")
    return 0 if not left else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
