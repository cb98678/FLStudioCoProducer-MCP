import json
import subprocess
import sys
from pathlib import Path

from test_flpfile import synthetic

from coproducer import flpfile as F

TOOL = Path(__file__).resolve().parents[1] / "tools" / "flp_tool.py"


def run(*args):
    return subprocess.run([sys.executable, str(TOOL), *map(str, args)], capture_output=True, text=True)


def test_add_notes_writes_pattern_and_clip_in_sandbox(tmp_path):
    src = tmp_path / "in.flp"
    src.write_bytes(synthetic())
    out = tmp_path / "sandbox" / "out.flp"
    out.parent.mkdir()
    notes = tmp_path / "n.json"
    notes.write_text(json.dumps({"channel": 7, "label": "SUB", "notes": [[0, 1, 36, 100], [4, 1, 36, 100]]}))
    r = run("add-notes", src, out, notes, "--base-id", 100)
    assert r.returncode == 0, r.stderr
    f = F.Flp.load(out)
    assert 100 in f.pattern_ids() and len(f.playlist_items()) == 3
    assert src.read_bytes() == synthetic()


def test_tool_refuses_to_write_outside_a_sandbox_folder(tmp_path):
    src = tmp_path / "in.flp"
    src.write_bytes(synthetic())
    r = run("enable", src, tmp_path / "out.flp", 3, "off")
    assert r.returncode != 0 and "sandbox" in (r.stderr + r.stdout)
    assert not (tmp_path / "out.flp").exists()
