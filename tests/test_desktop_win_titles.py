from coproducer.desktop_win import is_main_title


def test_only_the_main_window_counts():
    assert is_main_title("probe_scratch.flp - FL Studio 2026")
    assert is_main_title("FL Studio 2026")
    assert not is_main_title("Welcome to FL Studio")
    assert not is_main_title("Fruity Limiter (Insert 2)")
    assert not is_main_title("C:\\coproducer - FL Studio 2026")
