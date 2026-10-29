from coproducer.cli import numbering_cmd
from coproducer.result import ok


def test_lists_non_default_indexes_and_track_count():
    def call(name, **kw):
        table = {"op_patterns_pattern_count": 2, "op_patterns_pattern_number": 1, "op_playlist_track_count": 500}
        if name in table:
            return ok(table[name])
        i = kw.get("index")
        return ok({"op_patterns_get_pattern_name": "Pattern %d" % i, "op_patterns_get_pattern_length": 16,
                   "op_patterns_is_pattern_default": 0 if i in (1, 2) else 1, "op_playlist_get_track_name": "Track %d" % i}[name])
    r = numbering_cmd.numbering(call)
    assert r["non_default_indexes"] == [1, 2] and r["playlist_tracks"] == 500 and r["passed"]
    assert r["track_names"][500] == "Track 500"
