import json
import struct

import numpy as np

from coproducer import flpfile as F
from coproducer.services import set_service


def _template(path):
    head = b"FLhd" + struct.pack("<I", 6) + struct.pack("<HHH", 0, 1, 96)
    item = bytearray(88)
    item[6:8] = struct.pack("<H", 5)
    item[8:12] = struct.pack("<I", 384)
    item[12:14] = struct.pack("<H", 499)
    ev = [[199, F.enc16("26.1.7")], [156, struct.pack("<I", 120000)], [202, F.enc16("C:\\elsewhere\\")],
          [64, struct.pack("<H", 5)], [0, b"\x01"], [203, F.enc16("Ch5")], [196, F.enc16("C:\\old.wav")], [104, struct.pack("<H", 1)],
          [99, b"\x00\x00"], [233, bytes(item)]]
    path.write_bytes(F.emit(head, ev, b""))
    return str(path)


def _stub(tmp_path, desk, procs):
    (tmp_path / "recipes").mkdir(exist_ok=True)
    (tmp_path / "recipes" / "extract_stems_gui.json").write_text(json.dumps(
        {"name": "extract_stems_gui", "verified": True, "params": [], "steps": [{"do": "hotkey", "keys": ["f9"]}]}))
    set_service("recipes_dir", str(tmp_path / "recipes"))
    set_service("sandbox_root", str(tmp_path))
    set_service("procs", procs)
    set_service("fl_exe", "C:\\FL\\FL64.exe")
    desk.fake.main["title"] = "fl_stems_bench.flp - FL Studio 2026"


def test_extracts_in_fl_and_copies_the_four_stems(rig, desk, procs, wav, tmp_path):
    procs.open = False
    _stub(tmp_path, desk, procs)
    song = wav("song", 0.1 * np.ones((9600, 2)))
    out = tmp_path / "songs" / "x" / "stems" / "fl"

    def fl_separates(fake, ev):
        if ev == ("hotkey", ("f9",)):
            (out / "Audio").mkdir(parents=True, exist_ok=True)
            for part in ("drums", "bass", "instruments", "vocals"):
                (out / "Audio" / ("song_%s.wav" % part)).write_bytes(b"RIFF" + part.encode())
    desk.fake.reactions.append(fl_separates)
    r = rig.call("extract_stems_gui", path=song, out_dir=str(out), template=_template(tmp_path / "t.flp"), timeout_s=30)
    assert r.ok, r
    assert r.value["extracted"] and (out / "other.wav").read_bytes() == b"RIFFinstruments" and (out / "vocals.wav").read_bytes() == b"RIFFvocals"
    assert procs.log and procs.log[0][0] == "launch" and procs.log[0][2].endswith("fl_stems_bench.flp")
    again = rig.call("extract_stems_gui", path=song, out_dir=str(out), template=_template(tmp_path / "t.flp"))
    assert again.ok and again.value["extracted"] is False                    # reused: the four stems are newer than the song


def test_refuses_outside_and_times_out(rig, desk, procs, wav, tmp_path):
    procs.open = False
    _stub(tmp_path, desk, procs)
    song = wav("song", 0.1 * np.ones((9600, 2)))
    assert rig.call("extract_stems_gui", path=song, out_dir="/elsewhere/stems").error.code == "E_SANDBOX_VIOLATION"
    r = rig.call("extract_stems_gui", path=song, out_dir=str(tmp_path / "stems"), template=_template(tmp_path / "t.flp"), timeout_s=10)
    assert r.error.code == "E_TIMEOUT"
