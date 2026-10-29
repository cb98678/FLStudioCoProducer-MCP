import json

import numpy as np

from coproducer.services import set_service

RECT = (100, 50, 841, 667)


class FakeNewtime:
    """Just enough of Newtime for the marker step: grid, marker lines where Shift+clicks land, a scroll track that pages."""
    def __init__(self, duration, bpm, pps=145.7):
        self.duration, self.bar, self.pps, self.start, self.marks = duration, 240.0 / bpm, pps, 0.0, []
        self.span = (734 - 6) / pps
        self.per_px = (2 * duration - self.span) / 670        # Newtime's timeline runs about twice the sample

    def image(self):
        img = np.zeros((800, 1000, 3), dtype=np.uint8)
        l, t = RECT[0], RECT[1]
        img[t:RECT[3], l:RECT[2]] = (61, 78, 89)
        for n in range(int(self.duration / self.bar) + 2):
            x = int(round(l + 6 + (n * self.bar - self.start) * self.pps))
            if l + 6 <= x < l + 734:
                img[t + 143:t + 578, x] = (16, 38, 50)
        for m in self.marks:
            x = int(round(l + 6 + (m - self.start) * self.pps))
            if l + 6 <= x < l + 734:
                img[t + 143:t + 578, x] = (255, 184, 113)
        img[t + 600, l + 26:l + 714] = (50, 58, 63)
        h0 = int(round(l + 26 + self.start / self.per_px))
        img[t + 600, h0:h0 + 18] = (80, 89, 94)
        return img

    def react(self, fake, ev):
        if ev[0] == "click" and len(ev) == 6 and ev[5] == ("shift",):
            self.marks.append(self.start + (ev[1] - RECT[0] - 6) / self.pps)
        elif ev[0] == "click" and ev[2] == RECT[1] + 600:
            h0 = RECT[0] + 26 + self.start / self.per_px
            self.start += -16 / self.pps if RECT[0] + 7 <= ev[1] <= RECT[0] + 24 else (self.span if ev[1] > h0 + 18 else (-self.span if ev[1] < h0 else 0))
            self.start = min(max(0.0, self.start), 2 * self.duration - self.span)
        fake.image = self.image()


def _stub(tmp_path, desk):
    import shutil
    (tmp_path / "recipes").mkdir(exist_ok=True)
    (tmp_path / "recipes" / "newtime_load_gui.json").write_text(json.dumps({"name": "newtime_load_gui", "verified": True, "params": ["path", "bpm"],
                                                                            "steps": [{"do": "type", "text": "newtime_load_gui {path} {bpm}"}]}))
    (tmp_path / "recipes" / "newtime_quantize_save_gui.json").write_text(json.dumps(
        {"name": "newtime_quantize_save_gui", "verified": True, "params": ["out_path", "snap_row"],
         "steps": [{"do": "type", "text": "snap {snap_row}"}, {"do": "hotkey", "keys": ["ctrl", "s"]}, {"do": "type", "text": "{out_path}"},
                   {"do": "hotkey", "keys": ["enter"]}, {"do": "expect_file", "path": "{out_path}"}]}))
    set_service("recipes_dir", str(tmp_path / "recipes"))
    set_service("sandbox_root", str(tmp_path))
    desk.fake.main["rect"] = (0, 0, 1000, 800)
    desk.fake.dialogs.append({"handle": 300, "title": "WarpCorrectionTrack (Master)", "rect": RECT})
    nt = FakeNewtime(8.0, 120.0)
    desk.fake.image = nt.image()
    desk.fake.reactions.append(nt.react)
    desk.fake.script_dialog(("ctrl", "s"), "Save As", on_enter=lambda text: shutil.copy(str(tmp_path / "voice.wav"), text))
    return nt


def _syllables(wav):
    rate, rng = 48000, np.random.default_rng(5)
    x = np.zeros(rate * 8)
    for k in range(2, 28):
        i, n = int((k * 0.25 - 0.03 + rng.uniform(-0.012, 0.012)) * rate), int(0.16 * rate)
        env = np.minimum(1.0, np.arange(n) / (0.004 * rate)) * np.exp(-np.arange(n) / (0.08 * rate))
        x[i:i + n] += 0.4 * env * (np.sin(2 * np.pi * 220 * np.arange(n) / rate) + 0.3 * rng.standard_normal(n))
    return wav("voice", x, rate)


def test_detects_opens_marks_quantizes_and_saves(rig, desk, tmp_path, wav):
    nt = _stub(tmp_path, desk)
    src = _syllables(wav)
    r = rig.call("quantize_vocal_gui", path=src, out_path=str(tmp_path / "warped.wav"), bpm=120.0, division=2, grid_up=1, grid_down=1)
    assert r.ok, r
    assert r.value["verified"] == r.value["markers"] >= 15 and len(nt.marks) == r.value["markers"] and (tmp_path / "warped.wav").is_file()
    typed = [e[1] for e in desk.fake.log if e[0] == "type"]
    assert typed[0].startswith("newtime_load_gui ") and typed[0].endswith("warped_newtime_in.wav 120") and "snap 2" in typed


def test_refuses_and_stops_early(rig, desk, tmp_path, wav):
    _stub(tmp_path, desk)
    src = _syllables(wav)
    assert rig.call("quantize_vocal_gui", path=src, out_path=str(tmp_path / "o.wav"), bpm=120.0, division=5).error.code == "E_ARG"
    assert rig.call("quantize_vocal_gui", path=src, out_path="/elsewhere/o.wav", bpm=120.0).error.code == "E_SANDBOX_VIOLATION"
    desk.fake.dialogs.clear()
    r = rig.call("quantize_vocal_gui", path=src, out_path=str(tmp_path / "o.wav"), bpm=120.0)
    assert r.error.code == "E_GUI_MISMATCH" and "snap 4" not in [e[1] for e in desk.fake.log if e[0] == "type"]
