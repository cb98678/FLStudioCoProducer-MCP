"""Close FL (graceful, refuses with unsaved changes) and start it on a project.   python tools/fl_open.py PROJECT.flp"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from coproducer.config import load_config
from coproducer.procs import Procs
cfg = load_config(Path(__file__).resolve().parents[1])
p = Procs()
if p.fl_count() and not p.close_fl(30.0):
    print("FL did not close (a dialog may be open)"); sys.exit(1)
from coproducer.cli import detect
exe = cfg["fl"]["exe"] or str(detect.newest_fl_exe())
p.launch(exe, sys.argv[1])
print("launched", sys.argv[1])
