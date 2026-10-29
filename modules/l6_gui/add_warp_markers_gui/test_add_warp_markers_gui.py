"""A drawn stand-in for Newtime: blue-grey grid with dark bar lines, orange marker lines where Shift+clicks land, and a scroll handle that
pages the view when its track is clicked. The module has to read each view, click, check and page through the whole sample."""
import numpy as np

RECT = (100, 50, 841, 667)
BG, BAR, ORANGE, HANDLE, TRACK = (61, 78, 89), (16, 38, 50), (255, 184, 113), (80, 89, 94), (50, 58, 63)


class FakeNewtime:
    def __init__(self, duration, bpm, pps=145.7, drop_every=0):
        self.duration, self.bar, self.pps, self.start, self.marks, self.drop, self.clicks = duration, 240.0 / bpm, pps, 0.0, [], drop_every, 0
        self.span = (734 - 6) / pps
        self.per_px = (2 * duration - self.span) / ((714 - 26) - 18)     # Newtime's timeline runs about twice the sample

    def image(self):
        img = np.zeros((800, 1000, 3), dtype=np.uint8)
        l, t = RECT[0], RECT[1]
        img[t:RECT[3], l:RECT[2]] = BG
        for n in range(int(self.duration / self.bar) + 2):
            x = int(round(l + 6 + (n * self.bar - self.start) * self.pps))
            if l + 6 <= x < l + 734:
                img[t + 143:t + 578, x] = BAR
        for m in self.marks:
            x = int(round(l + 6 + (m - self.start) * self.pps))
            if l + 6 <= x < l + 734:
                img[t + 143:t + 578, x] = ORANGE
        img[t + 600, l + 26:l + 714] = TRACK
        h0 = int(round(l + 26 + self.start / self.per_px))
        img[t + 600, h0:h0 + 18] = HANDLE
        return img

    def react(self, fake, ev):
        if ev[0] == "click" and len(ev) == 6 and ev[5] == ("shift",):
            self.clicks += 1
            if not (self.drop and self.clicks % self.drop == 0):
                self.marks.append(self.start + (ev[1] - RECT[0] - 6) / self.pps)
        elif ev[0] == "click" and ev[2] == RECT[1] + 600:                       # the scroll bar: arrow or a page either side
            h0 = RECT[0] + 26 + self.start / self.per_px
            if RECT[0] + 7 <= ev[1] <= RECT[0] + 24:
                self.start -= 16 / self.pps
            elif ev[1] > h0 + 18:
                self.start += self.span
            elif ev[1] < h0:
                self.start -= self.span
            self.start = min(max(0.0, self.start), 2 * self.duration - self.span)
        fake.image = self.image()


def _install(desk, nt):
    desk.fake.main["rect"] = (0, 0, 1000, 800)
    desk.fake.dialogs.append({"handle": 300, "title": "WarpCorrectionTrack (Master)", "rect": RECT})
    desk.fake.image = nt.image()
    desk.fake.reactions.append(nt.react)


def test_places_every_marker_through_the_sample(rig, desk):
    nt = FakeNewtime(40.0, 130.0)
    _install(desk, nt)
    times = [round(0.5 + 0.37 * k, 3) for k in range(100)]
    r = rig.call("add_warp_markers_gui", markers=times, duration_s=40.0, bpm=130.0)
    assert r.ok, r
    assert r.value["placed"] == 100 and r.value["verified"] == 100 and r.value["views"] >= 7
    assert max(min(abs(m - t) for m in nt.marks) for t in times) < 0.01


def test_reports_markers_that_did_not_appear_and_refuses_a_resized_window(rig, desk):
    nt = FakeNewtime(12.0, 130.0, drop_every=4)
    _install(desk, nt)
    r = rig.call("add_warp_markers_gui", markers=[1.0, 2.0, 3.0, 4.0], duration_s=12.0, bpm=130.0)
    assert r.ok and r.value["placed"] == 4 and r.value["missed"] == [4.0]
    desk.fake.dialogs[0]["rect"] = (100, 50, 900, 700)
    assert rig.call("add_warp_markers_gui", markers=[1.0], duration_s=12.0, bpm=130.0).error.code == "E_GUI_MISMATCH"
