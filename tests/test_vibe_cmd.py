
from coproducer.cli import vibe_cmd
from coproducer.result import fail, ok


class Stub:
    """A stand-in for the registry call: records names, answers from a table, can fail one module."""

    def __init__(self, title="song.flp - FL Studio 2026", fail_on=None):
        self.names, self.title, self.fail_on = [], title, fail_on

    def __call__(self, name, **kw):
        self.names.append(name)
        if name == self.fail_on:
            return fail("E_GUI_MISMATCH", "stubbed failure")
        if name == "apply_gain_trim":
            return ok({"applied_delta_db": 3.0, "before_db": -3.37})
        if name == "op_mixer_get_eq_gain":
            return ok(0.5)
        table = {"check_desktop_ready": {"title": self.title}, "generate_audio": {"paths": ["/sb/gen/a.wav"]},
                 "build_measure_report": {"loudness": {"lufs": -20.0}}, "render_with_restart": {"path": "/sb/r.wav", "bridge_back_s": 3},
                 "estimate_bpm_dsp": {"bpm": 128.0, "candidates": []}, "estimate_key_dsp": {"key": "C"},
                 "critique_audio": {"source": "dsp", "observations": []}, "call_agent_llm": {"message": {"content": "", "tool_calls": []}}}
        return ok(table.get(name, {}))


def test_runs_every_step_in_order_and_checks_the_render_is_audible(tmp_path):
    call = Stub()
    r = vibe_cmd.vibe(call, tmp_path / "song.flp", tmp_path, "dark techno", track=2)
    assert r["passed"] and r["steps"]["audible"]["render_lufs"] == -20.0
    order = [n for n in call.names if n in ("generate_audio", "import_audio_clip_gui", "add_audio_clip_to_playlist_gui", "ensure_loop_mode", "save_sandbox_project", "render_with_restart")]
    assert order == ["generate_audio", "import_audio_clip_gui", "add_audio_clip_to_playlist_gui", "ensure_loop_mode", "save_sandbox_project", "render_with_restart"]


def test_refuses_another_open_project_and_stops_at_the_first_failure(tmp_path):
    call = Stub(title="mine.flp - FL Studio 2026")
    r = vibe_cmd.vibe(call, tmp_path / "song.flp", tmp_path, "x")
    assert not r["passed"] and "generate_audio" not in call.names and "open that sandbox project" in r["steps"]["project_open"]["error"]
    call = Stub(fail_on="add_audio_clip_to_playlist_gui")
    r = vibe_cmd.vibe(call, tmp_path / "song.flp", tmp_path, "x")
    assert not r["passed"] and "save_sandbox_project" not in call.names and "render_with_restart" not in call.names


def test_adjust_with_no_proposals_is_a_pass_and_with_only_unusable_ones_a_failure(tmp_path):
    call = Stub()
    r = vibe_cmd.vibe(call, tmp_path / "song.flp", tmp_path, "x", adjust=True)
    assert r["passed"] and r["steps"]["proposals"]["note"] == "the brain proposed no change"


def test_adjust_hands_the_polish_loop_keep_if_heard(tmp_path, monkeypatch):
    seen = {}

    def fake(call, project, work, bpm, keep, keep_if_heard=False):
        seen.update(keep=keep, keep_if_heard=keep_if_heard)
        return {"steps": {}, "passed": True, "report": {"loudness": {"lufs": -18.0}}}

    monkeypatch.setattr(vibe_cmd.polish_cmd, "polish", fake)
    r = vibe_cmd.vibe(Stub(), tmp_path / "song.flp", tmp_path, "x", adjust=True)
    assert seen == {"keep": False, "keep_if_heard": True} and r["passed"]
