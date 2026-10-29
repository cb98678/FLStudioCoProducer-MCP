import numpy as np

from coproducer import newtimeview as nv


def test_warp_markers_keep_small_moves_one_per_line_and_sane_stretches():
    step = 60 / 120 / 4                                   # 16ths at 120 bpm: 0.125 s
    onsets = [1.0 - 0.03, 1.125 - 0.031, 1.135 - 0.03, 1.5325, 2.0 - 0.06 + 0.011]
    got = nv.warp_markers(onsets, 120.0, lead_s=0.03, max_move_s=0.045, division=4)
    assert [round(g / step) for _, g in got] == [8, 9, 16]       # 1.5625 sits between two lines (too far); 1.135 loses line 9 to the closer onset
    assert nv.best_lead([t - 0.04 for t in np.arange(1, 5, 0.25)], 120.0) == 0.04


def test_bar_lines_skip_the_editor_edges_and_marker_columns():
    img = np.full((60, 400, 3), (61, 78, 89), dtype=np.uint8)
    img[:, 0] = img[:, 399] = (16, 38, 50)                # the editor's own dark edges
    for x in (50, 190, 330):
        img[:, x] = (16, 38, 50)
    img[:, 120] = (255, 184, 113)                          # a warp marker
    assert nv.bar_lines(img, (0, 60), (0, 400)) == [50.0, 190.0, 330.0]
    assert nv.marker_columns(img, (0, 60), (0, 400)) == [120.0]
