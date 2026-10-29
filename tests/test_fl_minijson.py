import json

import pytest
from hypothesis import given, settings, strategies as st

from coproducer.fl_minijson import _mj_dumps, _mj_loads

scalars = st.none() | st.booleans() | st.integers(-10**12, 10**12) | st.floats(allow_nan=False, allow_infinity=False) | st.text()
values = st.recursive(scalars, lambda c: st.lists(c, max_size=4) | st.dictionaries(st.text(max_size=8), c, max_size=4), max_leaves=12)


@settings(max_examples=300, deadline=None)
@given(values)
def test_roundtrip_matches_json(v):
    assert _mj_loads(_mj_dumps(v)) == v
    assert json.loads(_mj_dumps(v)) == v          # our output is valid JSON
    assert _mj_loads(json.dumps(v)) == v          # we read real JSON, with spaces and unicode escapes


def test_rejects_garbage():
    for bad in ("", "{", "[1,", '{"a" 1}', "tru", "[1] x"):
        with pytest.raises((ValueError, IndexError)):
            _mj_loads(bad)
