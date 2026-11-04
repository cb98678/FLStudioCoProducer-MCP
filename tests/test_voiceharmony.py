"""voiceharmony: a chord loop chosen from the voice's notes, the voice as a lead line in key."""
from coproducer import voiceharmony as vh


def test_the_loop_that_holds_the_voice_wins():
    # E minor: the voice sings E and B over bar 0, C and G over bar 1, G and D over bar 2, D and F sharp over bar 3 (i, VI, III, VII)
    sung = {0: (4, 11), 1: (0, 7), 2: (7, 2), 3: (2, 6)}
    w = {}
    for rep in range(4):
        for b, pcs in sung.items():
            row = [0.0] * 12
            for pc in pcs:
                row[pc] = 1.0
            w[rep * 4 + b] = row
    got = vh.best_loop(w, 4, "minor")
    assert got["name"] == "i-VI-III-VII" and got["bars_per_chord"] == 1 and got["roots8"][:4] == [4, 0, 7, 2]
    assert got["qualities"][4] == "min" and got["qualities"][0] == "maj"


def test_notes_land_on_the_remix_grid_and_the_lead_stays_in_key():
    notes = [{"start_s": 10.0, "end_s": 10.5, "pitch": 53, "velocity": 90}, {"start_s": 50.0, "end_s": 50.4, "pitch": 64, "velocity": 90}]
    clips = [[8, 2, 9.0, 12.0, "Verse", "phrase", "vocals"], [20, 0, 0.0, 5.0, "Other", "bars", "other"]]
    rows = vh.to_remix(notes, clips, origin_s=1.0, source_bpm=120.0)
    assert len(rows) == 1 and abs(rows[0][0] - (8 * 4 + 18 - 8)) < 1e-6     # beat 18 of the song is beat 10 past source bar 2
    lead = vh.lead_rows(rows, 4, "minor")
    assert lead[0][2] % 12 in {4, 6, 7, 9, 11, 0, 2} and 60 <= lead[0][2] <= 84   # F (53) snapped into E minor, an octave up


def test_snap_moves_only_what_is_out_of_key():
    assert vh.snap(64, 4) == 64 and vh.snap(65, 4) == 64 and vh.snap(63, 4) == 62


def test_midi_notes_read_a_newtone_file_at_the_bench_tempo(tmp_path):
    import mido
    mf = mido.MidiFile(ticks_per_beat=400)   # Newtone's Save as MIDI: 400 ticks a beat, no tempo message
    tr = mido.MidiTrack()
    tr.append(mido.Message("note_on", note=62, velocity=80, time=400))
    tr.append(mido.Message("note_off", note=62, velocity=0, time=400))
    mf.tracks.append(tr)
    mf.save(str(tmp_path / "nt.mid"))
    plain = vh.midi_notes(str(tmp_path / "nt.mid"))
    at130 = vh.midi_notes(str(tmp_path / "nt.mid"), bpm=130.0)
    assert plain == [{"start_s": 0.5, "end_s": 1.0, "pitch": 62, "velocity": 80}]           # mido assumes 120 bpm
    assert at130 == [{"start_s": round(60 / 130, 4), "end_s": round(120 / 130, 4), "pitch": 62, "velocity": 80}]
