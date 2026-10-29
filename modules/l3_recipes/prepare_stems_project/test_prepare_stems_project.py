import struct

import numpy as np

from coproducer import flpfile as F
from coproducer.services import set_service


def _template(path):
    head = b"FLhd" + struct.pack("<I", 6) + struct.pack("<HHH", 0, 2, 96)
    item = bytearray(88)
    item[6:8] = struct.pack("<H", 5)
    item[8:12] = struct.pack("<I", 384)
    item[12:14] = struct.pack("<H", 499)
    ev = [[199, F.enc16("26.1.7")], [156, struct.pack("<I", 120000)], [202, F.enc16("C:\\elsewhere\\")]]
    for c, smp in ((4, ""), (5, "C:\\old.wav")):
        ev += [[64, struct.pack("<H", c)], [0, b"\x01"], [203, F.enc16("Ch%d" % c)], [196, F.enc16(smp)], [104, struct.pack("<H", 1)]]
    ev += [[99, b"\x00\x00"], [233, bytes(item)]]
    path.write_bytes(F.emit(head, ev, b""))
    return str(path)


def test_writes_the_song_clip_and_the_data_folder(rig, wav, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    song = wav("song", np.zeros((48000 * 2, 2)))
    out = tmp_path / "songs" / "x" / "fl_stems" / "bench.flp"
    r = rig.call("prepare_stems_project", song=song, out_project=str(out), template=_template(tmp_path / "t.flp"))
    assert r.ok, r
    f = F.Flp.load(out)
    assert f.data_folder() == str(out.parent) + "\\" and f.channel_info(5)["sample"].endswith("song.wav") and r.value["channel"] == 5
    items = f.playlist_items()
    assert len(items) == 1 and struct.unpack("<I", items[0][8:12])[0] == 384     # 2 s at 120 bpm, 96 ppq
    assert r.value["expected"]["vocals"].endswith("Audio\\song_vocals.wav") or r.value["expected"]["vocals"].endswith("Audio/song_vocals.wav")
    assert r.value["ready"] is False


def test_refuses_outside_and_missing(rig, wav, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    song = wav("song", np.zeros((4800, 2)))
    assert rig.call("prepare_stems_project", song=song, out_project="/elsewhere/b.flp").error.code == "E_SANDBOX_VIOLATION"
    assert rig.call("prepare_stems_project", song=str(tmp_path / "none.wav"), out_project=str(tmp_path / "b.flp"),
                    template=_template(tmp_path / "t.flp")).error.code == "E_NOT_FOUND"
