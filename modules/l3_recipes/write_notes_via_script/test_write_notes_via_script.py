import json
import os
import sys
import types

from coproducer.services import set_service

NOTES = [{"pitch": 60, "start": 0, "duration": 1, "velocity": 100}, {"pitch": 64, "start": 1.5, "duration": 0.25}]


class FakeNote:
    pass


class FakeScore:
    PPQ = 96

    def __init__(self):
        self.notes, self.cleared = [], 0

    @property
    def noteCount(self):
        return len(self.notes)

    def clearNotes(self, all=False):
        self.notes, self.cleared = [], self.cleared + 1

    def addNote(self, n):
        self.notes.append(n)

    def getNote(self, i):
        return self.notes[i]


def run_script(text, cwd):
    fake = types.ModuleType("flpianoroll")
    fake.score, fake.Note = FakeScore(), FakeNote
    fake.ScriptDialog = lambda title, desc: (title, desc)
    sys.modules["flpianoroll"] = fake
    here = os.getcwd()
    os.chdir(cwd)  # FL runs piano roll scripts with the Piano roll scripts folder as the working directory
    try:
        ns = {}
        exec(compile(text, "script", "exec"), ns)
        ns["apply"](ns["createDialog"]())
        return fake.score
    finally:
        os.chdir(here)
        del sys.modules["flpianoroll"]


def test_installs_a_runnable_script(rig, tmp_path):
    folder = tmp_path / "Piano roll scripts"
    set_service("piano_roll_scripts_dir", str(folder))
    r = rig.call("write_notes_via_script", notes=NOTES)
    assert r.ok and r.meta["verified"] is True and r.value["expected"] == 2
    text = open(r.value["path"]).read()
    compile(text, "script", "exec", dont_inherit=True)
    score = run_script(text, folder)
    assert score.cleared == 1 and [(n.number, n.time, n.length) for n in score.notes] == [(60, 0, 96), (64, 144, 24)]
    assert round(score.notes[0].velocity, 3) == 0.787
    report = json.load(open(r.value["result_path"]))
    assert report["written"] == 2 and report["ppq"] == 96 and report["notes"][1][:3] == [64, 144, 24]
    assert os.path.dirname(r.value["result_path"]) == os.path.dirname(r.value["path"])


def test_invalid_notes_and_missing_folder(rig, tmp_path):
    assert rig.call("write_notes_via_script", notes=NOTES).error.code == "E_UNSUPPORTED_API"
    set_service("piano_roll_scripts_dir", str(tmp_path / "s"))
    assert rig.call("write_notes_via_script", notes=[{"pitch": 200, "start": 0, "duration": 1}]).error.code == "E_ARG"
    assert rig.call("write_notes_via_script", notes=[{"pitch": 60, "start": -1, "duration": 1}]).error.code == "E_ARG"
    assert not (tmp_path / "s").exists()
