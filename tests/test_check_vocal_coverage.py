"""tools/check_vocal_coverage.py: every word inside a clip, none twice, clips in order, gaps between clips."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("cvc", Path(__file__).resolve().parents[1] / "tools" / "check_vocal_coverage.py")
cvc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cvc)


def test_coverage_finds_missing_doubled_and_out_of_order_words():
    words = [{"start": 0.1, "end": 0.4}, {"start": 1.0, "end": 1.3}, {"start": 2.0, "end": 2.2}, {"start": 5.0, "end": 5.5}]
    spans = [(0.0, 1.5, 8.0), (1.2, 2.5, 12.0)]
    got = cvc.coverage(spans, words)
    assert [w["index"] for w in got["missing"]] == [3] and [w["index"] for w in got["twice"]] == [1] and got["in_order"]
    assert not cvc.coverage([(3.0, 6.0, 4.0), (0.0, 2.5, 8.0)], words)["in_order"]
    assert cvc.gaps([(0.5, 1.5, 8.0), (2.0, 3.0, 12.0)], 4.0) == [(0.0, 0.5), (1.5, 2.0), (3.0, 4.0)]
