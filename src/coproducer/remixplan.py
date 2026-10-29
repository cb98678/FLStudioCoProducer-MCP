"""A tech-house remix plan for a song with stems: sections, harmony, bass, stabs, vocal chops, drums and FX cues, all as plain data.

Nothing here touches a project file or audio. tools/build_techhouse.py turns the plan into a sandbox copy of an FL project, so every
part stays a pattern, a playlist clip or a sample the producer can edit.

Time is in bars and 16th-note steps of a 124 bpm 4/4 grid (bar numbers start at 0). Notes are (start_beat, dur_beats, key, velocity)
with key as FL's raw piano-roll number. Harmony is one 8-bar loop that follows the original chorus (A A A A B B E E), so a chorus
vocal placed at a bar that is a multiple of 8 sits on the chords the singer used.
"""
from __future__ import annotations

from . import arrange, drumplan, stylepack, tension
from .automation import db_to_fader

BPM = 124.0
SOURCE_BPM = 108.478
STRETCH = BPM / SOURCE_BPM  # tempo ratio applied to the vocal stem
BAR_BEATS = 4
ROOTS8 = (9, 9, 9, 9, 11, 11, 4, 4)  # pitch classes: A A A A B B E E
KEY_PC = 9  # A
MAJOR = (0, 4, 7)

SECTIONS = [
    {"name": "intro", "start": 0, "end": 8},
    {"name": "groove", "start": 8, "end": 24},
    {"name": "break", "start": 24, "end": 32},
    {"name": "build", "start": 32, "end": 40},
    {"name": "drop", "start": 40, "end": 56},
    {"name": "break", "start": 56, "end": 64},
    {"name": "build", "start": 64, "end": 72},
    {"name": "drop", "start": 72, "end": 96},
    {"name": "outro", "start": 96, "end": 104},
]
TOTAL_BARS = SECTIONS[-1]["end"]
ORIGIN_S = 27.3085  # seconds into the stems where bar 0 of the original sits (the first detected drum hit)
CHOP_EVENTS_OVERRIDE: list[tuple] | None = None  # set by songplan.apply when a plan lists its own chop placements
FX_CUES_OVERRIDE: list[dict] | None = None
CHOP_ROLES: dict | None = None
STYLE: dict | None = None  # a grammar style pack (stylepack.load) set by songplan.apply; None keeps the tech-house code below
PITCH_RATIO = 0.99424  # rubberband pitch ratio for the vocal stem: a tuning correction measured on the first song's stem (a plan sets its own, 1.0 by default)
VOCAL_MULTIPLE = 1.0  # the vocal runs at BPM * VOCAL_MULTIPLE (0.5: one vocal bar over two remix bars); see stylepack.vocal_multiple

# Mixer inserts used by the build (1..16 exist in every project) and the level each starts at, in dB. Set from stem renders (2026-10-23): the two Trance pluck
# patches are very quiet (peak -20 dBFS at 0 dB for a velocity-96 chord), so they sit at the top of the fader range with high velocities.
GROUPS = {
    "kick": (1, -3.0), "clap": (2, -4.0), "hats": (3, -6.0), "perc": (4, -10.0), "reese": (5, -5.0), "sub": (6, -4.0),
    "stab": (7, 5.0), "arp": (8, 3.0), "chops": (9, -1.0), "vocal": (10, -3.0), "fx": (11, -5.0),
    "orig": (12, -8.0),  # the original's instrumentation (Demucs "other"), under the remix parts; a first guess for gain staging to replace
    "pad": (13, 0.0),    # held pad chords under the stabs (a chords option with a pad layer); a first guess, the part-level loop sets it
}
# Song-form remixes (the original's instrumentation under the remix): the person's own balance on the techno remix (2026-10-26) raised the
# original's instruments 2.9 dB and lowered the FX bed 1.6 dB from the first guesses above.
SONG_FORM_DB = {"orig": -5.0, "fx": -6.5}
MASTER_DB = -3.0  # headroom: there is no limiter on the master yet


def fader_raw(db: float) -> int:
    """Raw mixer fader value for a level in dB (12800 is 0 dB)."""
    return int(round(db_to_fader(db) * 16000))


STUTTER = None  # a song-form plan's roll into the last drop: (chop name, remix bars, ((start, length) in bars, ...)); playlist audio clips of the vocal
KIT_PATHS: dict = {}  # a plan's kit: voice -> sample path (variety: a demo song's kit), used by the build in place of the synthesized one-shots
INSTRUMENTS: dict = {}  # a plan's instruments: variety sound role -> {"import": {...}, "register", "label"} (remixbuild.demo_instrument)
KEYS_NOTES: tuple = ()  # a plan's chord-synth part from the reference MIDI (songform.keys_notes); empty: the style's own chords
LEAD_NOTES: tuple = ()  # a plan's lead line (voiceharmony.lead_rows: the tuned voice's own notes in key), played by the arp channel instead of its arp
BAR_ROOTS: tuple = ()  # a song-form plan's root per remix bar (the original's chord on the bar it carries); None falls back to ROOTS8
BAR_SPLITS: tuple = ()  # a harmony loop's second chord per loop bar: (step, pitch class) or None (variety.harmony_splits)
PATTERN_BARS = 1  # a plan's longest pattern: 1 is one pattern per distinct bar; 16 is one piano roll per section, up to 16 bars (remixbuild.blocks)


def root_pc(bar: int, step: float = 0.0) -> int:
    """The chord root at a 16th step of a remix bar: the record's root on a bar it carries, else the loop's (its second chord from the
    split step on)."""
    if 0 <= bar < len(BAR_ROOTS) and BAR_ROOTS[bar] is not None:
        return BAR_ROOTS[bar]
    sp = BAR_SPLITS[bar % 8] if len(BAR_SPLITS) == 8 else None
    if sp is not None and step >= sp[0]:
        return int(sp[1])
    return ROOTS8[bar % 8]


def section_at(bar: int) -> dict:
    for s in SECTIONS:
        if s["start"] <= bar < s["end"]:
            return s
    raise ValueError("bar %d is outside the arrangement" % bar)


def sub_key(pc: int, octave: int = 1) -> int:
    """Raw key of the Remix Sub patch for a pitch class: it sounds raw - 7 semitones, so the key is MIDI + 7 (A1 = MIDI 33 = raw 40)."""
    return 12 * (octave + 1) + pc + 7


def reese_key(pc: int, octave_up: int = 0) -> int:
    """Sampler key for the reese pluck, which is recorded at A1 on key 60: the nearest transposition of the root, within a tritone."""
    d = (pc - KEY_PC + 6) % 12 - 6
    return 60 + d + 12 * octave_up


DIATONIC = False  # song-form plans: triads take their quality from the key (ii, iii and vi minor) since the roots follow the original's chords
MODE = "major"  # the key's mode, for scale-snapped arp cells and harp runs (a plan's "mode")
ROOT_QUALITY: dict = {}  # pitch class -> chord quality from a plan's harmony loop (variety); its third wins over DIATONIC
MINOR_QUALITIES = ("min", "min7", "madd9", "minmaj7", "min6")


def chord_keys(pc: int, base: int = 60) -> list[int]:
    """Raw keys of a triad for the Trance pluck patches (their raw key modulo 12 is the pitch class). base is a multiple of 12. A major triad,
    or with DIATONIC the key's own triad on that root (B minor in A major, D minor in A minor), so the remix chords agree with the original's; a plan's harmony
    loop (ROOT_QUALITY) names the quality of each root it uses."""
    if pc in ROOT_QUALITY:
        return [base + pc + i for i in ((0, 3, 7) if ROOT_QUALITY[pc] in MINOR_QUALITIES else MAJOR)]
    if DIATONIC and (pc - KEY_PC) % 12 in ((0, 5, 7) if MODE == "minor" else (2, 4, 9)):   # i, iv and v in a minor key (2026-10-29: was
        return [base + pc + i for i in (0, 3, 7)]                                             # the major key's ii, iii, vi, so A minor's i was A major)
    return [base + pc + i for i in MAJOR]


def chord_third(pc: int) -> int:
    k = chord_keys(pc)
    return k[1] - k[0]


def _clamp(notes: list[tuple]) -> list[tuple]:
    """Velocity into 1..127 (the tension.py generators ramp without a ceiling)."""
    return [(st, d, k, max(1, min(127, int(v)))) for st, d, k, v in notes]


def _bar_notes(bar: int, steps: tuple[int, ...], key: int, vel: int, dur: float = 0.4) -> list[tuple]:
    return [((bar * 16 + s) / 4, dur, key, vel) for s in steps]


def kick_beats(bar_from: int, bar_to: int, drums: drumplan.Plan) -> list[float]:
    return sorted({(b * 16 + s) / 4 for b, s, inst, *_ in drums.events if inst == "kick" and bar_from <= b < bar_to})


# ---- drums

def _groove(plan: drumplan.Plan, b: int, k: int, heavy: bool) -> None:
    """Tech-house bar: four on the floor, clap on 2 and 4, open hat off the beat, closed hat and shaker 16ths, a ghost rim."""
    plan.kick4(b)
    if k >= 2 or heavy:
        for s in (4, 12):
            plan.ev(b, s, "clap", 0.78)
    for s in (2, 6, 10, 14):
        plan.ev(b, s, "ohat", 0.72, 0.12 * (1 if s % 8 == 2 else -1))
    for s in range(16):
        if s % 4 != 2:
            plan.ev(b, s, "hat", (0.8 if s % 4 == 0 else 0.34 + 0.05 * ((s * 5) % 3)) * (1.0 if heavy else 0.85), 0.14 * (1 if s % 2 else -1))
    plan.shaker(b, 0.9 if heavy else 0.7)
    plan.ev(b, 7 if b % 2 else 15, "rim", 0.5 if heavy else 0.4)
    if b % 4 == 3:
        for s, key in ((14, 64), (14.5, 60), (15, 55)):
            plan.ev(b, s, "tom", 0.55, 0, key)


def _grammar() -> bool:
    return STYLE is not None and STYLE.get("engine") == "grammar"


def drums(sections: list[dict] | None = None) -> drumplan.Plan:
    """The drum plan. Intro, build and outro come from drumplan; groove, break and drop are tech-house. A grammar style pack writes its own."""
    secs = sections or SECTIONS
    if _grammar():
        return stylepack.drums(STYLE, secs)
    plan = drumplan.Plan()
    for s in secs:
        for b in range(s["start"], s["end"]):
            plan.labels[b] = s["name"]
            k = b - s["start"]
            if s["name"] in ("groove", "drop"):
                _groove(plan, b, k, heavy=s["name"] == "drop")
                if s["name"] == "drop" and k % 8 == 7 and b != s["end"] - 1:
                    plan.fill(b, "A")
            elif s["name"] == "break":
                plan.hats(b, "e8", 0.45 + 0.07 * k)
                for st in (4, 12):
                    plan.ev(b, st, "rim", 0.5)
                if k == s["end"] - s["start"] - 1:
                    plan.roll(b, 8, 16, 1, 0.25, 0.6)
            elif s["name"] == "intro":
                plan.hats(b, "e8" if k < 4 else "full", 0.7 + 0.05 * k)
                plan.shaker(b, 0.7 + 0.04 * k)
                if k >= 4:
                    plan.kick4(b, 0.8)
                    if k >= 6:
                        for st in (4, 12):
                            plan.ev(b, st, "clap", 0.6)
                if k == 7:
                    plan.roll(b, 12, 16, 1, 0.25, 0.6)
            elif s["name"] == "outro":
                n = s["end"] - s["start"]
                g = max(0.35, 1.0 - 0.09 * k)
                plan.kick4(b, g)
                plan.hats(b, "off", 0.8 * g)
                if k < 3:
                    for st in (4, 12):
                        plan.ev(b, st, "clap", 0.7 * g)
                if k == n - 1:
                    plan.events = [e for e in plan.events if not (e[0] == b and e[1] > 0 and e[2] == "kick")]
            else:
                drumplan._section(plan, s["name"], b, s["start"], s["end"])
    for b, g in drumplan.default_crashes(secs).items():
        plan.ev(b, 0, "crash", g, 0.15 if b % 8 else -0.15)
    return plan


# ---- bass and chords

def reese_notes() -> list[tuple]:
    if _grammar():
        return _clamp(stylepack.line_notes(STYLE, "bass", SECTIONS, root_pc, lambda pc, up: reese_key(pc, up), chord_third, KEY_PC))
    out: list[tuple] = []
    for s in SECTIONS:
        for b in range(s["start"], s["end"]):
            k = b - s["start"]
            key, hi = reese_key(root_pc(b)), reese_key(root_pc(b), 1)
            if s["name"] == "groove":
                steps = (2, 6, 10, 14) if k < 8 else (2, 6, 7, 10, 14, 15)
                out += _bar_notes(b, steps, key, 100 if k < 8 else 108)
                if k % 4 == 3:
                    out += _bar_notes(b, (11,), hi, 110)
            elif s["name"] == "drop":
                hard = s["start"] > 60
                steps = (1, 2, 3, 5, 6, 7, 9, 10, 11, 13, 14, 15) if hard else (2, 3, 6, 7, 10, 11, 14, 15)
                for i, st in enumerate(steps):
                    up = (i % 4 == 3) or (hard and st in (7, 15))
                    out += _bar_notes(b, (st,), hi if up else key, 120 if st % 4 == 2 else 96)
            elif s["name"] == "build":
                if b >= s["end"] - 3:
                    out += _bar_notes(b, tuple(range(2, 16, 2)) if b < s["end"] - 1 else (2, 6, 10), key, 100 + 6 * (b - (s["end"] - 3)))
            elif s["name"] == "outro" and b < s["start"] + 4:
                out += _bar_notes(b, (2, 6, 10, 14), key, 100 - 12 * (b - s["start"]))
    return _clamp(out)


def sub_notes(drum_plan: drumplan.Plan) -> list[tuple]:
    """Sub bass: gated off-beat notes in grooves and drops, pedal swells in breaks, the tension.py build gestures before drops. Cut where kicks land."""
    if _grammar():
        line = stylepack.line_notes(STYLE, "sub", SECTIONS, root_pc, lambda pc, up: sub_key(pc, 1 + up), chord_third, KEY_PC)
        if STYLE.get("sub_duck_kicks", True):
            line = tension.truncate_at_kicks(line, kick_beats(0, TOTAL_BARS, drum_plan), gap=0.05, min_len=0.2)
        return _clamp(line)
    out: list[tuple] = []
    for s in SECTIONS:
        n = s["end"] - s["start"]
        for b in range(s["start"], s["end"]):
            k = b - s["start"]
            key, hi = sub_key(root_pc(b)), sub_key(root_pc(b), 2)
            if s["name"] == "groove" and k >= 4:
                out += _bar_notes(b, (2, 6, 10, 14), key, 104, 0.9)
            elif s["name"] == "drop":
                out += _bar_notes(b, (2, 6, 10, 14), key, 118, 1.0)
                out += _bar_notes(b, (3, 7, 11, 15), key, 100, 0.4) if s["start"] > 60 else []
            elif s["name"] == "break":
                out += tension.pedal_swell(b, 1, key, v0=80 + 5 * k, ramp=0, octave_key=hi if k >= n // 2 else None, octave_from=0)
            elif s["name"] == "build":
                if k < n - 2:
                    out += tension.gated_sub(b, key, vel=92 + 4 * k)
                elif k == n - 2:
                    out += tension.sixteenth_gate(b, key)
                else:
                    out += tension.hold_before_drop(b, key, hi)
            elif s["name"] == "outro" and b < s["start"] + 4:
                out += _bar_notes(b, (2, 6, 10, 14), key, 100, 0.9)
    return _clamp(tension.truncate_at_kicks(out, kick_beats(0, TOTAL_BARS, drum_plan), gap=0.05, min_len=0.2))


STAB_OFFBEAT = (2, 6, 10, 14)  # the classic house off-beat: the 8th between kicks


def stab_notes(offbeat: bool = False) -> list[tuple]:
    """Chord stabs: syncopated 16ths in grooves and drops (steps 3, 6, 11, 14 or 3, 6, 10, 15), or with offbeat=True the plain off-beat 8ths (2, 6, 10, 14); a sustained chord in breaks.
    A plan with keys_notes (the song's chords and strum from an accepted reference MIDI) plays those instead."""
    if KEYS_NOTES:
        return _clamp([tuple(n) for n in KEYS_NOTES])
    if _grammar():
        return _clamp(stylepack.chord_notes(STYLE, SECTIONS, root_pc, chord_keys, KEY_PC, MODE))
    out: list[tuple] = []
    for s in SECTIONS:
        for b in range(s["start"], s["end"]):
            k = b - s["start"]
            keys = chord_keys(root_pc(b))
            if s["name"] == "groove" and k >= 8:
                steps = STAB_OFFBEAT if offbeat else (3, 6, 11, 14) if b % 2 == 0 else (3, 6, 11, 15)
            elif s["name"] == "drop":
                steps = STAB_OFFBEAT if offbeat else (3, 6, 11, 14) if b % 2 == 0 else (3, 6, 10, 15)
            elif s["name"] == "break":
                steps = (0,)
            else:
                continue
            dur = 3.6 if s["name"] == "break" else 0.4
            for st in steps:
                for kk in keys:
                    out.append(((b * 16 + st) / 4, dur, kk, 108 if s["name"] != "drop" else 122))
    return _clamp(out)


def pad_notes() -> list[tuple]:
    """Held pad chords under the stabs, from a chords option with a pad layer (stylepack.pad_notes); none without one."""
    if not _grammar() or not STYLE.get("pad"):
        return []
    return _clamp(stylepack.pad_notes(STYLE, SECTIONS, root_pc, chord_keys, KEY_PC, MODE))


def arp_notes() -> list[tuple]:
    """A rising 16th arpeggio through the breaks and builds (tension.rising_arp), one chord per bar; a plan's lead_notes (the voice doubled
    in key) instead when it has them."""
    if LEAD_NOTES:
        return _clamp([tuple(n) for n in LEAD_NOTES])
    if _grammar():
        return _clamp(stylepack.arp_notes(STYLE, SECTIONS, root_pc, chord_keys, KEY_PC, MODE))
    out: list[tuple] = []
    for s in SECTIONS:
        if s["name"] not in ("break", "build"):
            continue
        n = s["end"] - s["start"]
        start = s["start"] + (n // 2 if s["name"] == "break" else 0)
        chords = [chord_keys(root_pc(b), 72) + [chord_keys(root_pc(b), 84)[0]] for b in range(start, s["end"])]
        out += tension.rising_arp(start, chords, v0=64, bar_ramp=int(60 / len(chords)))
    return _clamp(out)


# ---- vocal chops

# Chops: name -> hints in the ORIGINAL vocal stem, in seconds. The hints only say where to look: tools/techhouse_audio.py moves the start onto the nearest
# syllable onset and the end onto the nearest word onset ("word") or the end of the sung phrase ("phrase", for a last word that must ring out), then
# checks the cut. max_gap shortens a long silence inside the chop. Whisper times are off by up to half a second, so never trust them as cut points.
CHOPS = {
    "hook": {"start": 133.55, "end": 137.05, "end_mode": "word", "words": "i got friends in low places", "prev": "cause", "after": "the whiskey"},
    "friends": {"start": 134.05, "end": 134.45, "end_mode": "word", "words": "friends", "prev": "got", "next": "in"},
    "lowplaces": {"start": 135.15, "end": 137.05, "end_mode": "word", "words": "low places", "prev": "in", "after": "the whiskey"},
    "whiskey": {"start": 137.65, "end": 138.70, "end_mode": "word", "words": "whiskey", "prev": "the", "next": "drowns"},
    "drowns": {"start": 137.66, "end": 139.60, "end_mode": "word", "words": "whiskey drowns", "prev": "the", "next": "and the beer"},
    "bluesaway": {"start": 141.80, "end": 143.20, "end_mode": "phrase", "max_gap": 0.35, "words": "my blues away", "prev": "beer chases"},  # ends where the voice stops
    "blues": {"start": 141.80, "end": 142.50, "end_mode": "word", "words": "my blues", "prev": "beer chases", "next": "away"},
    "okay": {"start": 145.90, "end": 148.20, "end_mode": "phrase", "words": "i'll be okay"},
    "oasis": {"start": 69.00, "end": 70.70, "end_mode": "word", "words": "oasis", "prev": "to the", "after": "cause"},
    "pickup": {"start": 132.90, "end": 133.90, "end_mode": "word", "words": "cause i've got", "next": "friends"},
}
# Chops that also get an echo version (name_echo): a 3/16 ping-pong echo baked into the sample.
ECHOED = ("hook", "bluesaway", "drowns", "friends", "okay", "whiskey")


FRIENDS_ROLES = {  # which chop plays which part, for arrange.arrange_chops
    "teasers": ["blues", "friends_echo", "lowplaces"], "hook": "hook", "hook_echo": "hook_echo", "groove_answers": ["bluesaway_echo", "whiskey", "bluesaway", "drowns_echo"],
    "groove_tail": "friends_echo", "stutter_a": "whiskey", "stutter_b": "blues", "stab": "friends", "stab_echo": "friends_echo", "drop_answers": ["bluesaway_echo", "drowns"],
    "closers": ["okay", "okay_echo"], "outro_closer": "okay_echo",
}


def chop_events() -> list[tuple]:
    """(bar, step, chop name, velocity 1..127, key). Teasers in the intro, the hook through the groove, pitched stutters in builds, the hook on the drops.
    A loaded song plan supplies its own rows or chop roles (songplan.apply); the table below is the first song's hand-made one."""
    if CHOP_EVENTS_OVERRIDE is not None:
        return list(CHOP_EVENTS_OVERRIDE)
    if CHOP_ROLES is not None:
        return arrange.arrange_chops(SECTIONS, CHOP_ROLES)
    e: list[tuple] = []
    # intro teasers
    e += [(5, 8, "blues", 70, 60), (6, 12, "friends_echo", 80, 60), (7, 0, "lowplaces", 85, 60)]  # a quarter bar earlier than it was: its "s" now rings to the end of the bar, clear of the first hook
    # groove: the hook every 4 bars, answers between
    for b in (8, 12, 16, 20):
        e.append((b, 0, "hook", 108, 60))
    for b, name in ((10, "bluesaway_echo"), (14, "whiskey"), (18, "bluesaway"), (22, "drowns_echo")):
        e.append((b, 8, name, 96, 60))
    e.append((23, 8, "friends_echo", 100, 67))  # a quarter bar earlier: the full "friends" would sound over the break clip's pick-up
    # builds: a stutter that climbs a semitone a bar, then 16th stabs
    for first in (32, 64):
        for i in range(6):
            e.append((first + i, 0, "whiskey", 82 + 4 * i, 60 + i))
            e.append((first + i, 8, "blues", 78 + 4 * i, 60 + i))
        e += [(first + 6, s, "friends", 88 + 2 * s, 66) for s in range(0, 12, 4)]
        e.append((first + 6, 12, "friends_echo", 112, 66))
        e += [(first + 7, s, "friends", 100 + 2 * s // 2, 72) for s in (0, 2, 4, 6, 8, 10, 12)]
    # drops: hook, answer, hook, tail. The last hook of a drop is dry and the last answer is left out: the closing "okay" then lands on clear air, because a
    # hook_echo tail and an answer on top of it sounded muddy (Chops 22, user listening notes 2026-10-23). The first drop closes on the dry "okay": the
    # break that follows opens with the verse's pick-up half a bar early, and an echo tail would bleed into it.
    for first, n in ((40, 16), (72, 24)):
        last = first + n - 4
        for b in range(first, first + n, 4):
            e.append((b, 2, "hook_echo" if (b - first) % 8 == 4 and b != last else "hook", 112, 60))
            if b != last:
                e.append((b + 2, 10, "bluesaway_echo" if (b - first) % 8 == 0 else "drowns", 100, 60))
        e.append((first + n - 2, 0, "okay" if first == 40 else "okay_echo", 100, 60))
    # (the 16th chatter on friends and blues through bars 80 to 87 was removed: cluttered and inaudible, it did not give the high-pitched gabber stab it aimed for)
    e.append((98, 0, "okay_echo", 80, 60))
    return sorted(e)


# Long vocal clips from the stretched stem: (remix bar, orig bar that sits on it, orig start hint s, orig end hint s, label, end mode). The orig bar anchors the stem's
# own bar grid (origin_s + bar * 240 / SOURCE_BPM) to a bar of the remix. Start and end are snapped like the chops (onset in, gap or word onset out).
VOCAL_CLIPS = [
    (24, 48, 132.90, 148.20, "Vocal chorus (break)", "phrase"),
    (56, 16, 61.40, 78.20, "Vocal verse (break 2)", "phrase"),
    (72, 48, 132.90, 143.86, "Vocal chorus (drop 2)", "phrase"),
]
# Expected words at the two edges of each long clip, for the recogniser check (same order as VOCAL_CLIPS).
CLIP_WORDS = [
    {"head": "cause i've got friends", "tail": "i'll be okay"},
    {"head": "well i'm not big", "tail": "low places"},
    {"head": "cause i've got friends", "tail": "my blues away"},
]


def chop_conflicts(events: list[tuple], dry: dict[str, float], full: dict[str, float], bar_s: float | None = None, extra: list[tuple[str, float, float]] | None = None) -> list[str]:
    """Where chops sound on top of each other. events are chop_events() rows; dry[name] is the length of the chop itself and full[name] its length with the echo
    tail (both seconds, in the remix's time). extra adds (label, start_s, end_s) spans, the long vocal clips. A chop may start while an earlier one's echo tail
    still rings, but not while its dry part still sounds; and no chop may ring into the next section. Returns one line per problem."""
    bar_s = bar_s or 240.0 / BPM
    spans = sorted(((bar * 16 + step) * bar_s / 16, name) for bar, step, name, *_ in events)
    out: list[str] = []
    for i, (t0, name) in enumerate(spans):
        t_dry, t_full = t0 + dry[name], t0 + full[name]
        for t1, other in spans[i + 1 :]:
            if t1 >= t_dry - 0.05:
                break
            if other == name:
                continue  # a stutter retriggers its own chop on purpose
            out.append("%s at %.2f s starts %.2f s before %s's dry part ends" % (other, t1, t_dry - t1, name))
        bar = int(t0 / bar_s)
        sec = section_at(bar)
        if t_dry > sec["end"] * bar_s + 0.05:
            out.append("%s at bar %d runs into the next section by %.2f s" % (name, bar, t_dry - sec["end"] * bar_s))
        elif t_full > sec["end"] * bar_s + 0.3:
            out.append("%s at bar %d: echo tail runs %.2f s into the next section" % (name, bar, t_full - sec["end"] * bar_s))
    for label, a, b in extra or []:
        for t0, name in spans:
            if t0 < b and t0 + dry[name] > a and name != "":
                out.append("%s overlaps the %s clip by %.2f s" % (name, label, min(b, t0 + dry[name]) - max(a, t0)))
    return out


def chop_names() -> list[str]:
    """Every sample name the plan uses: each chop plus the echo versions."""
    return list(CHOPS) + [n + "_echo" for n in ECHOED]


def fx_cues() -> list[dict]:
    """Impacts, reverse sweeps, noise and tone risers, downlifters. Gains are dB; levels over time belong to automation.
    A loaded plan's own list wins; without one, a plan with roles gets arrange.generate_fx_cues; the table below is the first song's."""
    if FX_CUES_OVERRIDE is not None:
        return list(FX_CUES_OVERRIDE)
    if CHOP_ROLES is not None:
        return arrange.generate_fx_cues(SECTIONS)
    c: list[dict] = []
    for d in (40, 72):
        c += [{"kind": "impact", "bar": d, "gain_db": 0.0}, {"kind": "air_sweep", "bar": d - 1, "beats": 8, "gain_db": -3.0}]
    for d, g in ((8, -9.0), (24, -9.0), (56, -6.0), (96, -9.0)):
        c.append({"kind": "impact", "bar": d, "gain_db": g, "seconds": 2.2})
    for first in (32, 64):
        c += [{"kind": "noise_riser", "bar": first, "bars": 8, "f0": 400, "f1": 15000, "gain_db": -10.0},
              {"kind": "tone_riser", "bar": first, "bars": 8, "f0": 220.0, "f1": 1760.0, "gain_db": -20.0}]
    c += [{"kind": "noise_riser", "bar": 28, "bars": 4, "f0": 300, "f1": 9000, "gain_db": -15.0},
          {"kind": "noise_riser", "bar": 4, "bars": 4, "f0": 500, "f1": 7000, "gain_db": -18.0},
          {"kind": "noise_riser", "bar": 60, "bars": 4, "f0": 300, "f1": 9000, "gain_db": -15.0}]
    for d in (24, 56, 96):
        c.append({"kind": "downlifter", "bar": d, "beats": 8, "gain_db": -12.0})
    return c


def summary() -> dict:
    plan = drums()
    return {
        "bars": TOTAL_BARS,
        "seconds": round(TOTAL_BARS * 4 * 60 / BPM, 1),
        "drum_events": len(plan.events),
        "reese": len(reese_notes()),
        "sub": len(sub_notes(plan)),
        "stab": len(stab_notes()),
        "arp": len(arp_notes()),
        "chops": len(chop_events()),
        "fx_cues": len(fx_cues()),
    }
