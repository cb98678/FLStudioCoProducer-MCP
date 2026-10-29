"""Write the demo study pages: docs/demo_study/<song>.md for each FL demo song (what it does and how, measured, the data) and
docs/DEMO_STUDY.md (the findings across songs and the option bank's catalog). Run from the repo root after the study data, the
measurements or the bank change:

    python tools/demo_study_docs.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "src"))
from coproducer import variety  # noqa: E402

STUDY = HOME / "docs" / "demo_study"
BANK = variety.load_bank()
SRC = variety.sources(which=("songs",))   # the demo songs; remix studies have pages of their own
INS = json.loads((STUDY / "insights.json").read_text(encoding="utf-8"))["songs"]
FULL = json.loads((STUDY / "measure_full.json").read_text(encoding="utf-8")) if (STUDY / "measure_full.json").is_file() else {}
SOLO = json.loads((STUDY / "solo_measure.json").read_text(encoding="utf-8")) if (STUDY / "solo_measure.json").is_file() else {}
ASPECTS = (("form", "Form"), ("rhythm", "Rhythm and drums"), ("bass", "Bass"), ("harmony", "Harmony"), ("sounds", "Sounds and synths"),
           ("vocals", "Vocal production"), ("mix", "Mix and sidechain"), ("automation", "Automation"), ("transitions", "Transitions"))


def same_song(a: str, b: str) -> bool:
    """Render copies and study files name a song slightly differently (an accent dropped, a name cut at 60 characters)."""
    na, nb = ("".join(c for c in x.lower() if c.isalnum()) for x in (a, b))
    k = min(len(na), len(nb))
    return bool(na) and (na == nb or (k >= 16 and na[:k] == nb[:k]))   # a short title (LeriQ SHINE) matches in full


def data(sid: str) -> dict:
    return json.loads((STUDY / "data" / (SRC[sid]["data"] + ".json")).read_text(encoding="utf-8"))


def measured(sid: str) -> dict | None:
    want = SRC[sid]["data"]
    for k, v in FULL.items():
        if same_song(k, want):
            return v
    return None


def runs(prog: list[dict], n: int = 24) -> str:
    out, last = [], None
    for p in prog[:n]:
        key = "%s (%s)" % (p["chord"], p["roman"]) if p["chord"] else "none"
        if out and last == key:
            out[-1][1] += p["bars"]
        else:
            out.append([key, p["bars"]])
        last = key
    return ", ".join("%s x%d" % (k, b) for k, b in out)


def table(rows: list[list], head: list[str]) -> list[str]:
    out = ["| " + " | ".join(head) + " |", "| " + " | ".join("---" for _ in head) + " |"]
    for r in rows:
        out.append("| " + " | ".join(str(x).replace("|", "/") if x is not None else "" for x in r) + " |")
    return out


def option_link(oid: str) -> str:
    try:
        o = variety.find(BANK, oid)
    except variety.VarietyError:
        return "`%s`" % oid
    return "`%s` (%s)" % (oid, o["label"])


def same_key(a: str, b: str) -> bool:
    """Two key names for the same pitches (C# minor and Db minor, or a relative major and minor)."""
    alias = {"Db": "C#", "D#": "Eb", "Gb": "F#", "G#": "Ab", "A#": "Bb"}
    names = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]

    def pc(k: str) -> int | None:
        root, _, mode = k.partition(" ")
        root = alias.get(root, root)
        return None if root not in names else (names.index(root) + (3 if mode == "minor" else 0)) % 12
    return bool(a and b) and pc(a) == pc(b)


def key_notes(d: dict) -> list:
    """Lines on what the key readings say: the master pitch, the render's key when it differs, muted MIDI and its bounces."""
    out, k, ak = [], d.get("key") or {}, (d.get("audio_key") or {}).get("key")
    if k.get("written"):
        out.append("The notes are written in %s, but the project's master pitch is %+d cents, so it sounds (and renders) in %s."
                   % (k["written"], k["master_pitch_cents"], k["key"]))
    if ak and k.get("key") and not same_key(ak, k["key"]):
        out.append("The render's audio reads %s (a chroma vote over the first two minutes, margin %s; it often lands a fifth away on bass-heavy"
                   " mixes): not settled without listening." % (ak, (d.get("audio_key") or {}).get("margin")))
    mp = d.get("muted_parts") or []
    if d.get("muted_clips"):
        out.append("%d playlist clips are muted and play nothing; the readings above leave them out%s%s." % (
            d["muted_clips"], (": " + ", ".join("%s (%d muted notes, %d playing)" % (x["name"], x["muted_notes"], x["playing_notes"]) for x in mp[:6])) if mp else "",
            ("; the song plays audio bounces (%s), so the muted MIDI is likely their score" % ", ".join(d["bounces"][:3])) if d.get("bounces") and mp else ""))
    return [" ".join(out), ""] if out else []


def song_page(sid: str) -> str:
    s, d, ins = SRC[sid], data(sid), INS.get(sid, {})
    L = ["# %s - %s" % (s["artists"], s["title"]), "",
         "FL Studio 2026 demo project `%s`, studied on a sandbox copy (the original is untouched). Genre as the project names it: %s." % (s["file"], s["genre"] or "none"), ""]
    ak = d.get("audio_key") or {}
    L += table([[d["bpm"], d["key"].get("key"), ak.get("key", "-"), d["bars"], "%d:%02d" % divmod(int(d["seconds"]), 60), d["fl_version"], d["ppq"]]],
               ["Tempo", "Key (from the notes)", "Key (from the render)", "Bars", "Length", "Saved in FL", "PPQ"]) + [""]
    L += key_notes(d)
    if ins.get("summary"):
        L += [ins["summary"], ""]
    L += ["## What it does and how", ""]
    for key, title in ASPECTS:
        if ins.get(key):
            L += ["**%s.** %s" % (title, ins[key]), ""]
    if ins.get("rework_lessons"):
        L += ["**What the rework changes and keeps.**", ""] + ["- " + x for x in ins["rework_lessons"]] + [""]
    m = measured(sid)
    if m:
        p = m.get("pump_loudest_section") or {}
        L += ["## How it sounds (measured on the full render)", ""]
        if any((a.get("name") or "").lower().startswith("tempo") for a in d["automation"]):
            L += ["The project automates its tempo, so section times after the first change are approximate (bars are placed at the starting tempo).", ""]
        L += table([[m["lufs"], m["true_peak_db"], m["lra"], m["crest_db"], m["width_db"], m["low_width_db"], m["centroid_hz"], p.get("depth_db")]],
                   ["LUFS", "True peak dB", "LRA LU", "Crest dB", "Width (side/mid dB)", "Width under 120 Hz", "Centroid Hz", "Pump dB (loudest section)"]) + [""]
        b = m["bands"]
        L += ["Band balance (dB of the total): " + ", ".join("%s %s" % (k, v) for k, v in b.items()) + ".", ""]
        if m.get("sections"):
            L += table([[x["name"] or "", x["start_bar"], x["bars"], x["lufs"], x["centroid_hz"], x["width_db"], x["bands"]["sub"], x["bands"]["air"]] for x in m["sections"]],
                       ["Section", "Bar", "Bars", "LUFS", "Centroid", "Width", "Sub dB", "Air dB"]) + [""]
    solos = [v for v in SOLO.values() if same_song(v.get("song", ""), s["data"]) and (v.get("describe") or {}).get("notes") and not v.get("silent")
             and (v.get("peak_db") if v.get("peak_db") is not None else -999) > -45]
    if solos:
        L += ["## How its instruments sound (solo renders, soundbrief.describe)", ""]
        rows = []
        for v in solos:
            ds = v["describe"]
            rows.append([v["name"], v["role"], ", ".join(v.get("plugins") or []), ds.get("attack_s"), ds.get("decay_s"), ds.get("sustain"), ds.get("centroid_hz"),
                         (ds.get("register") or {}).get("median"), (ds.get("width") or {}).get("word"), "; ".join((ds.get("words") or [])[:3])])
        L += table(rows, ["Part", "Role", "Plugin", "Attack s", "Decay s", "Sustain", "Centroid Hz", "Register", "Width", "In words"]) + [""]
    L += ["## The data", "", "**Sections** (from the markers, or 8-bar phrases merged by what plays):", ""]
    L += table([[i + 1, x["start_bar"], x["bars"], x["name"], x["energy"], ", ".join(x["roles"])] for i, x in enumerate(d["sections"])],
               ["#", "Bar", "Bars", "Name", "Energy", "Plays"]) + [""]
    L += ["**Harmony** (a chord per bar from every pitched part): " + runs(d["progression"]), ""]
    if d["drums"]:
        L += ["**Drums** (each voice's 16th grid: X in most bars, x in many, o in some; late is the average offset in 16ths):", ""]
        L += table([[r["voice"], r["name"], "`%s`" % r["pattern"], r["hits_per_bar"], r["late_16ths"], r["velocity"], r["bars"]] for r in d["drums"] if r["bars"] >= 4][:24],
                   ["Voice", "Channel", "Pattern", "Hits a bar", "Late", "Velocity", "Bars"]) + [""]
    parts = [p for p in d["parts"] if p["role"] not in ("drums", "control") and (p["notes"] or p["clips"])]
    parts.sort(key=lambda p: -(p["notes"] or 0))
    L += ["**Parts** (role read from names and notes; plugin, FLEX preset, insert chain):", ""]
    L += table([[p["role"], p["name"], p["plugin"] or p["sample"], p["preset"], " > ".join(p["chain"] or [])[:90], "-".join(p["range"] or []), p["polyphony"], p["notes"]]
                for p in parts[:30]], ["Role", "Name", "Plugin or sample", "Preset", "Insert chain", "Range", "Poly", "Notes"]) + [""]
    rolls = [p for p in parts if p.get("bar")][:6]
    if rolls:
        L += ["**Typical bars** (two bars from each part's busiest bar, a 16th a column, - holds):", ""]
        for p in rolls:
            L += ["%s, %s (%s), from bar %d:" % (p["role"], p["name"], p["plugin"] or p["sample"], p["bar"]["from_bar"]), "", "```"] + p["bar"]["roll"] + ["```", ""]
    buses = [x for x in d["mixer"] if x["fed_by"] or x["index"] == 0]
    if buses:
        L += ["**Mixer buses and the master:**", ""]
        for x in buses[:16]:
            L.append("- %s %s%s: %s" % (x["index"], x["name"] or "", " (fed by %s)" % x["fed_by"] if x["fed_by"] else "",
                                         " > ".join(y["plugin"] + (" (%s)" % y["name"] if y.get("name") else "") for y in x["slots"]) or "no effects"))
        L.append("")
    if d["automation_summary"]:
        L += ["**Automation:** %d clips, by target: %s." % (len(d["automation"]), ", ".join("%s %d" % kv for kv in list(d["automation_summary"].items())[:8])), ""]
    if d["kit"]:
        L += ["**Kit** (the most played sample of each voice): " + "; ".join("%s %s" % (v, rows[0]["sample"].rsplit("\\", 1)[-1]) for v, rows in d["kit"].items()) + ".", ""]
    if ins.get("take"):
        L += ["## What it adds to the option bank", ""] + ["- " + option_link(o) for o in ins["take"]] + [""]
    return "\n".join(L) + "\n"


FINDINGS = """## What the twenty songs teach, across songs

**No two songs share a form.** The earlier remixes all used one template (intro, groove, break, an 8-bar riser build, a drop with chop
games, repeat, outro). The demos use at least eleven: additive 8-bar blocks with one long drop (Exoplanet), a journey with a vocal
breakdown (With You), Intro, V1, Drop 1, V2, Mid 8, Mid 8 Ramp, Drop 2, Re-Intro (NIGHT TERROR), loop blocks where the drums drop out
every third block (Mic Check Ready), verse and chorus with no riser at all (Right Night Feeling, Use Me, Bien Duro), filters instead of
drops (Africa's Calling), a half-time switch (Thief), entries and exits only (Inner Days), meter and tempo changes for scenes (Secret Agent
Rendezvous). The form is now a choice (form options) and the builds before choruses follow it.

**The groove is the genre.** Every song's drum grid is different in a way that names its genre: the dembow's 3-3-2, afro house's
three-step kick with percussion a third of a 16th late, drill's snare on 3 with uneven counter hats, trance's three-of-four hats, trip
hop's hand drums with velocity curves, lo-fi's swung ghosts. Seventeen grooves are in the bank, with triplet and swing support.

**Bass lines are melodies with rules.** Off-beat house pockets are one of fourteen designs: the rolling trance 16ths with a minor
seventh, a 16th ostinato on four layers, an octave bounce, a pop bass on the root and the fifth below, a dotted 3-3-2, a reggaeton bounce,
a long 808 that steps to the flat second, a log drum answering late, a bass that only answers with a Phrygian approach note.

**Layers make sounds.** Big sounds are stacks of plain ones: three kicks, three or six claps nudged apart, eight synths of three kinds on
one trance lead, four bass layers each covering a band, seven 3x Osc channels on one Layer. The bank's sound options import these
stacks (up to three channels) as the remix's instruments.

**Harmony is mostly colour.** Most loops are four chords or fewer; what changes is the colour: sevenths and ninths, sus2 and sus4 on the
same root (Song For You cycles one chord through four colours), a Dorian IV or a Phrygian bII borrowed into minor, a minor chord with a
major seventh for a spy cue. The remix keeps the record's own chords and changes voicing and rhythm; the harmony options are for new
sections and for records with no chords.

**The pump is a choice, not a default.** Measured on the loudest section of each render, the synth band's swing over one beat ranges
from 0.9 dB (Exoplanet) to 13.2 dB (Future House). Club records pump hard (Future House 13.2, Thief 12.1, Use Me 7.9, NIGHT TERROR 7.7),
songs barely pump (Right Night Feeling 1.9, Time 1.6, Secret Agent 1.2). The mix options set it per song, including no pump at all.

**Space is designed.** Sidechain is made six different ways (an envelope controller, a peak controller from the kick, a silent ghost
trigger, Gross Beat, a limiter keyed from a bus of kick and snare, a vocal ducking the leads); vocal stacks have their own bus trees;
one song uses a single hall for everything, another a global reverb shared by eight buses.

**Movement lives in automation.** Exoplanet has 85 clips, I'm Awake 93, With You 71: filters opening over 16 to 260 beats, pluck decays
ridden longer, FLEX macros moving, reverb rising for a breakdown and thrown out for the drop, delay throws on phrase ends, a tempo clip
for a new scene.

**Reading a project is not hearing it.** Three things in the files change what the notes say. Clips can be muted in the playlist (item
flag 0x2000, which PyFLP does not decode): Mic Check Ready mutes 120 of its 434 clips, its pad and piano MIDI among them, because the song
plays audio bounces of those parts (Piano (Rendered), Melody (Resampled)); SHINE mutes 57. Seven solo renders whose clips all carried the flag came out digitally
silent, and the same parts rendered again with only their own clips unmuted had sound: that is how the flag was confirmed. The readers
now leave muted clips out (the muted MIDI of a bounced part is still listed, marked muted, for its patch). The master pitch knob moves every note: both Inner Days
projects are written in D minor with the master at -400 cents and sound in Bb minor, which the render's own key confirms. And the key
from the notes and the key from the render agree on 12 of the 20 songs (the same scale or its relative), Bien Duro's render is a near tie
between F major and the notes' F minor, four land a fifth apart (Future House, Madonna, Stroll Up, Thief), where a chroma vote on a
bass-heavy mix is weak, and NIGHT TERROR, Mic Check Ready and SHINE differ more and are not settled without listening. Each song page
shows both.

**Loudness depends on the genre.** From -6.0 LUFS (Exoplanet, With You) and -6.5 (I'm Awake) to -15.1 (SHINE) and -16.4 (Secret Agent
Rendezvous). The targets for a remix follow its genre and the person's references, not one club number.
"""


def catalog() -> str:
    L = ["# The FL Studio demo songs, studied", "",
         "Twenty demo projects that ship with FL Studio 2026 (`C:\\Program Files (x86)\\Image-Line\\FL Studio 2026\\Data\\Demo projects\\Demo songs`),",
         "read on sandbox copies on 2026-10-28: every channel, pattern, clip, mixer insert and automation clip from the project file (flpfile, anatomy,",
         "projmusic), a full-mix render of each copy measured (loudness, crest, width, band balance, pump depth), and 146 solo renders (8 to 16",
         "bars each) of the songs' main parts and of every instrument in the bank, measured with soundbrief.describe: 142 have sound; two FL Keys",
         "parts render silent alone (Song For You's plays through a vocoder that needs the vocal; Stroll Up's is not explained) and two Bien Duro",
         "parts sit under -45 dB (one is a sidechain trigger channel, the other is not explained). The person asked for it: \"look at these songs, examine them deep, what they do, how",
         "they do it, how they sound, the design of the synths, everything, and develop all of the elements into choices and options in the",
         "recipes\" (2026-10-27). No lyrics are copied; the notebooks and comments in the projects are not reproduced.", "",
         "The result is the option bank (`src/coproducer/data/options`, %d options in %d categories), the variety engine that chooses from it per song"
         % (sum(len(v) for v in BANK.values()), len(BANK)),
         "(`src/coproducer/variety.py`, skill `creative-variety`), fifteen new style packs, and one page per song in `docs/demo_study`.", ""]
    rows = []
    for sid, s in SRC.items():
        m = measured(sid) or {}
        rows.append(["[%s - %s](demo_study/%s.md)" % (s["artists"], s["title"], s["data"]), s["genre"], s["bpm"], s["key"], "%d:%02d" % divmod(int(s["seconds"]), 60),
                     m.get("lufs"), (m.get("pump_loudest_section") or {}).get("depth_db"), m.get("lra")])
    L += ["## The songs", ""] + table(rows, ["Song", "Genre", "Bpm", "Key", "Length", "LUFS", "Pump dB", "LRA"]) + [""]
    L += [FINDINGS, ""]
    plugins, fx = Counter(), Counter()
    for sid in SRC:
        d = data(sid)
        plugins.update(d.get("plugins", {}))
        fx.update(d.get("effects", {}))
    L += ["## Instruments and effects the demos use", "",
          "Instrument plugins by how many parts use them: " + ", ".join("%s %d" % kv for kv in plugins.most_common(24)) + ".", "",
          "Effects by how many slots hold them: " + ", ".join("%s %d" % kv for kv in fx.most_common(30)) + ".", ""]
    L += ["## The option bank", "",
          "Each option names the songs it came from. `engine` is what the build realizes; options marked manual describe a move the agent makes",
          "with the modules after the build (apply_fx_chain, create_send_route, add_automation_clip).", ""]
    names = {"form": "Forms", "drums": "Grooves", "kit": "Drum kits", "bass": "Bass lines", "chords": "Chord treatments", "arp": "Arps and sequences",
             "harmony": "Harmony", "sound": "Instruments", "fx": "Transitions", "mix": "Mix architecture", "vocal": "Vocal production", "automation": "Automation moves"}
    for cat in ("form", "drums", "bass", "chords", "arp", "harmony", "sound", "kit", "fx", "mix", "vocal", "automation"):
        L += ["### %s (%d)" % (names[cat], len(BANK.get(cat, []))), ""]
        for o in BANK.get(cat, []):
            src = ", ".join(sorted({SRC[x["song"]]["title"] for x in o.get("sources", []) if x["song"] in SRC}))
            extra = " Manual: %s" % o["manual"] if o.get("manual") else ""
            L.append("- `%s` **%s.** %s%s%s" % (o["id"], o["label"], o["what"], " From: %s." % src if src else "", extra))
        L.append("")
    return "\n".join(L) + "\n"


def main() -> int:
    for sid in SRC:
        (STUDY / (SRC[sid]["data"] + ".md")).write_text(song_page(sid), encoding="utf-8", newline="\n")
    (HOME / "docs" / "DEMO_STUDY.md").write_text(catalog(), encoding="utf-8", newline="\n")
    print("wrote %d song pages and docs/DEMO_STUDY.md" % len(SRC))
    return 0


if __name__ == "__main__":
    sys.exit(main())
