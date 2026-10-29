"""Read the music out of an FL project file, without FL: every note where the playlist really plays it, what each channel is for (drums, bass,
chords, lead, arp, pad, vocal, FX), the drum grooves, the key and the chord per bar, and the arrangement as sections with the parts each one uses.

Written for the study of the 20 FL demo projects (2026-10-27, docs/DEMO_STUDY.md), and kept general: any project FL 12 to 26 saved. Read only.

Facts it relies on, read from those projects:
- Notes are 24-byte records in event 224, positions in the project's own PPQ (96 in most, 72 in an FL 20.8 save).
- A pattern clip plays its pattern from a start to an end offset in ticks (playlist item bytes 24 and 28, int32; -1 and -1 mean the whole
  pattern), and repeats that window when the clip is longer than it. A pattern's own length is its last note end rounded up to a bar.
- Playlist items are 32, 60, 80 or 88 bytes by FL version (flpfile.PLAYLIST_ITEM_SIZES); the fields used here sit at the same offsets.
"""
from __future__ import annotations

import math
import re
import struct
from collections import Counter, defaultdict

from . import flpfile
from .flpfile import Flp

NOTE_NAMES = ("C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")
# Krumhansl-Kessler key profiles (major, minor), the usual reference for key finding from pitch-class durations.
KK_MAJOR = (6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88)
KK_MINOR = (6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17)
CHORDS = {"": (0, 4, 7), "m": (0, 3, 7), "7": (0, 4, 7, 10), "maj7": (0, 4, 7, 11), "m7": (0, 3, 7, 10), "sus2": (0, 2, 7), "sus4": (0, 5, 7),
          "dim": (0, 3, 6), "add9": (0, 4, 7, 2), "madd9": (0, 3, 7, 2), "6": (0, 4, 7, 9), "m6": (0, 3, 7, 9), "5": (0, 7)}
ROMAN = ("I", "bII", "II", "bIII", "III", "IV", "#IV", "V", "bVI", "VI", "bVII", "VII")

# Substrings of a channel or sample name (lowercase, letters and digits only) that name a drum voice, checked in this order.
DRUM_SUBSTR = (("ohat", ("openhat", "ohat", "openhh", "oh0", "oh1")), ("hat", ("closedhat", "chat", "hihat", "hat", "hh0", "hh1", "hh")),
               ("kick", ("kick", "kik", "bassdrum", "bd0", "bd1")), ("snare", ("snare", "snr", "sd0", "sd1")), ("clap", ("clap", "clp", "snap")),
               ("rim", ("rimshot", "rim", "stick")), ("shaker", ("shaker", "shake", "tamb", "maracas", "cabasa")), ("ride", ("ride",)),
               ("crash", ("crash", "cymbal", "cym", "splash", "china")), ("tom", ("tom",)),
               ("perc", ("perc", "conga", "bongo", "timbal", "woodhit", "wood", "block", "cowbell", "clave", "guiro", "agogo", "triangle",
                         "logdrum", "click", "icecrack", "fpc", "drum", "djembe", "tabla")))
CONTROL_PLUGINS = ("MIDI Out", "Fruity Envelope Controller", "Fruity Keyboard Controller", "Fruity X-Y Controller", "Fruity Formula Controller")
ROLE_WORDS = [("vocal", ("vocal", "vox", "voc", "chop", "acapella", "adlib", "verse", "chorus", "rap", "choir", "singer", "lyric")),
              ("fx", ("riser", "rise", "sweep", "impact", "downlift", "uplift", "lifter", "noise", "sfx", "fx", "reverse", "whoosh",
                      "boom", "atmos", "texture", "vinyl", "foley", "tapestop", "transition", "build up", "white")),
              ("bass", ("808", "bass", "sub", "reese", "lowend")),
              ("pad", ("pad", "string", "drone", "ambient", "atmo", "choir")),
              ("chords", ("chord", "keys", "piano", "rhodes", "organ", "epiano", "stab", "guitar", "gtr", "harp", "wurli", "clav")),
              ("arp", ("arp",)),
              ("lead", ("lead", "pluck", "bell", "flute", "synth", "melody", "hook", "whistle", "brass", "horn", "sax", "violin",
                        "kalimba", "marimba", "mallet", "trumpet", "sitar", "koto", "pan", "oboe", "clarinet"))]
SECTION_WORDS = (("intro", ("intro",)), ("verse", ("verse", "rap")), ("pre", ("pre",)), ("build", ("build", "riser", "rise", "lift")),
                 ("drop", ("drop", "chorus", "hook")), ("break", ("break", "bridge", "interlude", "middle", "switch")),
                 ("outro", ("outro", "end", "tail")))


def _flat(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def drum_voice(name: str) -> str | None:
    """The drum voice a channel or sample name points at, or None. Keys of four letters or fewer must be a whole word or a word followed by
    digits ("tom2", "hh01"), so "custom", "trim" or "Bella" do not count."""
    flat, words = _flat(name), _words(name)
    for voice, keys in DRUM_SUBSTR:
        for k in keys:
            if len(k) > 4:
                if k in flat:
                    return voice
            elif any(w == k or (w.startswith(k) and w[len(k):].isdigit()) or (k == "hat" and w.endswith("hat")) for w in words):
                return voice
    return None


# Keys that count only as a whole word ("reverse" is not a verse, "subtle" not a sub).
WORD_ONLY = {"verse", "rap", "hook", "sub", "pan", "chop", "voc", "vox", "fx", "sfx", "arp", "mel", "hit", "boom", "white", "keys", "lyric"}


def _role_from_words(text: str) -> str | None:
    flat, w = _flat(text), _words(text)
    for role, kws in ROLE_WORDS:
        for k in kws:
            k2 = _flat(k)
            if (len(k2) <= 3 or k2 in WORD_ONLY) and any(x == k2 or (x.startswith(k2) and x[len(k2):].isdigit()) for x in w):
                return role
            if len(k2) > 3 and k2 not in WORD_ONLY and k2 in flat:
                return role
    return None


def classify(ch: dict, notes: list) -> str:
    """drums, bass, chords, pad, lead, arp, vocal, fx, control, audio or other: from the channel's name, its sample, its channel-rack group,
    its plugin, and what its notes do (register, how many sound at once, how long, how many different keys)."""
    name = (ch.get("name") or "") + " " + (ch.get("sample") or "")
    group = (ch.get("group") or "").lower()
    if ch.get("plugin") in CONTROL_PLUGINS:
        return "control"
    if ch.get("type") == "audio clip":
        flat = _flat(name)
        if drum_voice(ch.get("name") or "") and not any(k in flat for k in ("bass", "sub", "vocal", "vox", "riser", "sweep")):
            return "drums"                                   # one-shot drums placed as audio clips ("808 Snare" rolls, "Grv Kick")
        r = _role_from_words(name)
        if r in ("vocal", "fx", "bass"):
            return r
        if "vocal" in group or "vox" in group:
            return "vocal"
        if drum_voice(name):
            return "drums"
        return "audio"
    keys = [n[2] for n in notes]
    lens = sorted(n[3] for n in notes)
    one_shot = bool(notes) and len(set(keys)) <= 3 and lens[len(lens) // 2] <= 0.5
    if ch.get("type") == "sampler" and (drum_voice(name) and (one_shot or not notes)):
        return "drums"
    if any(g in group for g in ("drum", "perc")) and (one_shot or not notes):
        return "drums"
    if ch.get("plugin") in ("BooBass", "Transistor Bass"):
        return "bass"
    if any(g in group for g in ("vocal", "vox", "chop")):
        return "vocal"
    poly = polyphony(notes)
    med = sorted(keys)[len(keys) // 2] if keys else 60
    r = _role_from_words(name)
    if r and not (r == "bass" and med > 62 and poly > 1.5) and not (r == "lead" and med < 45 and poly < 1.3):
        return r
    if group and any(g in group for g in ("bass", "808")):
        return "bass"
    if group and any(g in group for g in ("fx", "sfx")):
        return "fx"
    if not notes:
        return "other"
    if one_shot and ch.get("type") == "sampler" and drum_voice(name):
        return "drums"
    if one_shot and ch.get("type") == "sampler" and med >= 55 and len(notes) > 8:
        return "drums"
    if med < 48 and poly < 1.5:
        return "bass"
    if poly >= 2.4:
        return "chords"
    if poly < 1.4 and lens[len(lens) // 2] <= 0.3 and len(notes) > 32:
        return "arp"
    return "lead"


def polyphony(notes: list) -> float:
    """Average number of notes starting together (within a 32nd), over the onsets that have any."""
    if not notes:
        return 0.0
    groups = Counter(round(n[0] * 8) for n in notes)
    return sum(groups.values()) / len(groups)


def song_notes(f: Flp, muted: bool = False) -> dict[int, list]:
    """Every note the current arrangement plays, per channel: (start_beats, channel, key, length_beats, velocity), in song time. muted=True
    adds the notes of clips muted in the playlist (a producer often bounces a part to audio and mutes its MIDI: the muted notes are its score)."""
    ppq = f.ppq
    pats = f.pattern_notes()
    plen = {}
    for pid, notes in pats.items():
        end = max((n[0] + max(n[3], 1) for n in notes), default=0)
        plen[pid] = max(ppq * 4, int(math.ceil(end / (ppq * 4.0))) * ppq * 4)
    out: dict[int, list] = defaultdict(list)
    for it in f.playlist_items():
        ref = struct.unpack_from("<H", it, 6)[0]
        if ref <= flpfile.PATTERN_BASE or (Flp.item_muted(it) and not muted):   # a clip muted in the playlist does not play
            continue
        pid = ref - flpfile.PATTERN_BASE
        notes = pats.get(pid)
        if not notes:
            continue
        pos, length = struct.unpack_from("<I", it, 0)[0], struct.unpack_from("<I", it, 8)[0]
        s, e = struct.unpack_from("<ii", it, 24) if len(it) >= 32 else (-1, -1)
        if s < 0 or e <= s:
            s, e = 0, plen[pid]
        win = e - s
        if win <= 0 or length <= 0:
            continue
        reps = int(math.ceil(length / float(win)))
        for r in range(reps):
            base = pos + r * win
            for npos, ch, key, ln, vel in notes:
                if s <= npos < e:
                    t = base + (npos - s)
                    if t < pos + length:
                        out[ch].append((t / ppq, ch, key, max(ln, 1) / ppq, vel))
    for ch in out:
        out[ch].sort()
    return dict(out)


def audio_regions(f: Flp) -> dict[int, list]:
    """Audio clips per channel as (start_beats, length_beats)."""
    out: dict[int, list] = defaultdict(list)
    for c in f.audio_clips():
        out[c["channel"]].append((c["pos"] / f.ppq, c["length"] / f.ppq))
    return dict(out)


def find_key(notes_by_ch: dict, roles: dict) -> dict:
    hist = [0.0] * 12
    for ch, notes in notes_by_ch.items():
        if roles.get(ch) in ("drums", "fx", "audio", "other"):
            continue
        for n in notes:
            hist[n[2] % 12] += min(n[3], 4.0)
    if sum(hist) == 0:
        return {"key": None}
    best = []
    for tonic in range(12):
        for mode, prof in (("major", KK_MAJOR), ("minor", KK_MINOR)):
            rot = [prof[(i - tonic) % 12] for i in range(12)]
            best.append((_corr(hist, rot), tonic, mode))
    best.sort(reverse=True)
    r, tonic, mode = best[0]
    return {"key": "%s %s" % (NOTE_NAMES[tonic], mode), "tonic": tonic, "mode": mode, "confidence": round(r, 3),
            "runner_up": "%s %s" % (NOTE_NAMES[best[1][1]], best[1][2])}


def _corr(a, b) -> float:
    ma, mb = sum(a) / 12.0, sum(b) / 12.0
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) or 1.0
    return num / den


def chord_of(weights: list, bass_pc: int | None) -> tuple[str | None, float]:
    """Best chord label for a pitch-class weight vector; the bass note breaks ties toward a root position."""
    total = sum(weights)
    if total <= 0:
        return None, 0.0
    best = (0.0, None)
    for root in range(12):
        for q, iv in CHORDS.items():
            pcs = {(root + i) % 12 for i in iv}
            inside = sum(weights[p] for p in pcs) / total
            score = inside - 0.08 * len(pcs) + (0.12 if bass_pc == root else 0.0) + (0.03 if q in ("", "m") else 0.0)
            if score > best[0]:
                best = (score, NOTE_NAMES[root] + q)
    return best[1], round(best[0], 2)


def chords_per_bar(notes_by_ch: dict, roles: dict, bars: int, beats_per_bar: int = 4) -> list:
    harm = {ch for ch, r in roles.items() if r in ("chords", "pad", "lead", "arp", "bass", "other")}
    out = []
    for b in range(bars):
        lo, hi = b * beats_per_bar, (b + 1) * beats_per_bar
        w = [0.0] * 12
        low = None
        for ch in harm:
            for n in notes_by_ch.get(ch, []):
                st, ln = n[0], n[3]
                ov = min(hi, st + ln) - max(lo, st)
                if ov > 0:
                    w[n[2] % 12] += ov * (1.5 if roles[ch] in ("chords", "pad") else 1.0)
                    if roles[ch] == "bass" and (low is None or n[2] < low[0]):
                        low = (n[2], n[2] % 12)
        out.append(chord_of(w, low[1] if low else None)[0])
    return out


def roman(chord: str | None, tonic: int, mode: str) -> str | None:
    if not chord:
        return None
    m = re.match(r"([A-G][#b]?)(.*)", chord)
    root = NOTE_NAMES.index(m.group(1))
    q = m.group(2)
    deg = ROMAN[(root - tonic) % 12]
    return (deg.lower() if q.startswith("m") and not q.startswith("maj") else deg) + (q[1:] if q.startswith("m") and not q.startswith("maj") else q)


def groove(notes: list, beats_per_bar: int = 4, steps: int = 16) -> dict:
    """Onset grid of a drum voice over the bars it plays: the share of those bars with a hit on each 16th, as a pattern string
    (X over 75 %, x over 40 %, o over 15 %), plus how far hits sit from the grid (late, in 16ths: positive means behind the beat)."""
    if not notes:
        return {}
    step_beats = beats_per_bar / float(steps)
    by_bar: dict[int, set] = defaultdict(set)
    off = []
    for n in notes:
        b = int(n[0] // beats_per_bar)
        q = (n[0] - b * beats_per_bar) / step_beats
        k = int(round(q)) % steps
        by_bar[b].add(k)
        off.append(q - round(q))
    nb = len(by_bar)
    share = [sum(1 for s in by_bar.values() if k in s) / float(nb) for k in range(steps)]
    pat = "".join("X" if v >= 0.75 else "x" if v >= 0.4 else "o" if v >= 0.15 else "." for v in share)
    trip = _triplet_hits(notes, beats_per_bar)
    out = {"pattern": pat, "bars": nb, "hits_per_bar": round(len(notes) / float(nb), 2), "late_16ths": round(sum(off) / len(off), 3),
           "velocity": [min(n[4] for n in notes), max(n[4] for n in notes)], "triplet_share": round(len(trip) / float(len(notes)), 2)}
    if len(trip) >= 0.5 * len(notes):  # a triplet voice (afro house percussion, a trap hat roll): its grid is 12 or 24 a bar, not 16
        t_bar: dict[int, set] = defaultdict(set)
        on12 = [n[0] for n in notes if abs(n[0] / (beats_per_bar / 12.0) - round(n[0] / (beats_per_bar / 12.0))) < 0.08]
        for st in on12:   # every hit on the triplet grid, the on-beat ones too
            b = int(st // beats_per_bar)
            t_bar[b].add(int(round((st - b * beats_per_bar) / (beats_per_bar / 12.0))) % 12)
        sh = [sum(1 for v in t_bar.values() if k in v) / float(len(t_bar)) for k in range(12)]
        out["triplet_pattern"] = "".join("X" if v >= 0.75 else "x" if v >= 0.4 else "o" if v >= 0.15 else "." for v in sh)
    return out


def _triplet_hits(notes: list, beats_per_bar: int = 4) -> list[float]:
    """Starts that sit on the bar's triplet-8th grid and clearly off its 16th grid."""
    out = []
    for n in notes:
        q16 = n[0] / (beats_per_bar / 16.0)
        q12 = n[0] / (beats_per_bar / 12.0)
        if abs(q12 - round(q12)) < 0.08 and abs(q16 - round(q16)) > 0.2:
            out.append(n[0])
    return out


def section_names(markers: list) -> list:
    out = []
    for m in markers:
        nm = (m.get("name") or "").lower()
        kind = next((k for k, ws in SECTION_WORDS if any(w in nm for w in ws)), None)
        out.append({"bar": m["bar"], "name": m.get("name"), "kind": kind})
    return out


def activity(notes_by_ch: dict, audio: dict, roles: dict, bars: int, beats_per_bar: int = 4) -> list:
    """Per bar: the roles playing and the note count, the arrangement's energy map."""
    rows = [{"roles": Counter(), "notes": 0} for _ in range(bars)]
    for ch, notes in notes_by_ch.items():
        for n in notes:
            b = int(n[0] // beats_per_bar)
            if 0 <= b < bars:
                rows[b]["roles"][roles.get(ch, "other")] += 1
                rows[b]["notes"] += 1
    for ch, regs in audio.items():
        for st, ln in regs:
            for b in range(int(st // beats_per_bar), int(math.ceil((st + ln) / beats_per_bar))):
                if 0 <= b < bars:
                    rows[b]["roles"][roles.get(ch, "audio")] += 1
    return rows


def _block_sig(act: list, s: int, e: int) -> tuple:
    roles: Counter = Counter()
    notes = 0
    for b in range(s, e):
        roles.update(act[b]["roles"])
        notes += act[b]["notes"]
    n = max(1, e - s)
    return frozenset(r for r, c in roles.items() if c / n >= 1 and r != "control"), notes / float(n)


def segment(act: list, markers: list, phrase: int = 8) -> list:
    """Sections: the project's own markers when it has at least two; else phrases of `phrase` bars (4 for short songs), with neighbours that
    use the same parts at a similar density (within 30 %) merged, which is how the songs studied are built (8-bar phrases)."""
    bars = len(act)
    if len(markers) >= 2:
        starts = sorted({max(0, int(round(m["bar"] - 1))) for m in markers} | {0})
    else:
        ph = phrase if bars >= 48 else 4
        blocks = [(s, min(bars, s + ph)) for s in range(0, bars, ph)]
        starts, prev = [], None
        for s, e in blocks:
            sig = _block_sig(act, s, e)
            if prev is None or sig[0] != prev[0] or not (0.7 <= (sig[1] + 1) / (prev[1] + 1) <= 1.3):
                starts.append(s)
                prev = sig
    starts = [s for s in starts if s < bars]
    out = []
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else bars
        roles, dens = _block_sig(act, s, e)
        out.append({"start_bar": s + 1, "bars": e - s, "roles": sorted(roles), "density": round(dens, 1)})
    if out:
        hi = max(x["density"] for x in out) or 1.0
        for x in out:
            x["energy"] = round(x["density"] / hi, 2)
    if markers and len(markers) >= 2:
        names = section_names(markers)
        for sec in out:
            m = next((x for x in names if int(round(x["bar"])) == sec["start_bar"]), None)
            if m:
                sec["name"], sec["kind"] = m["name"], m["kind"]
    return out


def read(f: Flp, rep: dict) -> dict:
    """The musical reading of a project: rep is anatomy.read(f) of the same file."""
    chans = {c["id"]: c for c in rep["channels"]}
    notes = song_notes(f)
    for c in rep["channels"]:                                  # a Layer channel plays its children: give them its notes
        if c.get("type") == "layer" and notes.get(c["id"]):
            for kid in c.get("children") or []:
                notes.setdefault(kid, [])
                notes[kid] = sorted(notes[kid] + [(n[0], kid, n[2], n[3], n[4]) for n in notes[c["id"]]])
    audio = audio_regions(f)
    roles = {cid: classify(c, notes.get(cid, [])) for cid, c in chans.items() if c.get("type") not in ("automation", "layer")}
    cur = next((a for a in rep["arrangements"] if a["current"]), rep["arrangements"][0] if rep["arrangements"] else {"bars": 0, "markers": []})
    bars = int(math.ceil(cur["bars"] or 0))
    key = find_key(notes, roles)
    chords = chords_per_bar(notes, roles, bars) if key.get("key") else []
    key, chords = sounding(key, chords, f.main_pitch())     # the master pitch knob moves what the notes sound like
    act = activity(notes, audio, roles, bars)
    sections = segment(act, cur.get("markers", []))
    drums: dict[str, dict] = {}
    for cid, r in roles.items():                              # drums placed as audio clips count as hits at each clip start
        if r == "drums" and audio.get(cid) and not notes.get(cid):
            notes[cid] = [(st, cid, 60, ln, 100) for st, ln in audio[cid]]
    for cid, r in roles.items():
        if r == "drums" and notes.get(cid):
            v = drum_voice(chans[cid].get("name") or "") or drum_voice(chans[cid].get("sample") or "") or "perc"
            g = groove(notes[cid])
            g["channel"] = chans[cid].get("name")
            g["sample"] = chans[cid].get("sample")
            g["notes"] = len(notes[cid])
            g["layers"] = drums.get(v, {}).get("layers", []) + [chans[cid].get("name")]
            if g["bars"] >= drums.get(v, {}).get("bars", 0):          # the channel playing the most bars speaks for the voice (not a roll)
                drums[v] = g
            else:
                drums[v]["layers"] = g["layers"]
    parts = []
    for cid, r in sorted(roles.items()):
        ns = notes.get(cid, [])
        c = chans[cid]
        if not ns and not audio.get(cid):
            continue
        keys = [n[2] for n in ns]
        lens = sorted(n[3] for n in ns)
        parts.append({"channel": cid, "name": c.get("name"), "role": r, "type": c.get("type"), "plugin": c.get("plugin"), "sample": c.get("sample"),
                      "group": c.get("group"),
                      "insert": c.get("insert"), "notes": len(ns), "clips": len(audio.get(cid, [])),
                      "range": [min(keys), max(keys)] if keys else None, "median_key": keys[len(keys) // 2] if keys else None,
                      "polyphony": round(polyphony(ns), 2), "median_len_beats": round(lens[len(lens) // 2], 3) if lens else None,
                      "first_bar": int(min([n[0] for n in ns] + [a[0] for a in audio.get(cid, [])]) // 4) + 1})
    prog = []
    for c in chords:
        if not prog or prog[-1][0] != c:
            prog.append([c, 1])
        else:
            prog[-1][1] += 1
    return {"bars": bars, "key": key, "chords_per_bar": chords,
            "progression": [{"chord": c, "roman": roman(c, key["tonic"], key["mode"]) if key.get("key") else None, "bars": n} for c, n in prog],
            "drums": drums, "parts": parts, "sections": sections, "roles": Counter(roles.values())}


def transpose_chord(chord: str | None, semis: int) -> str | None:
    """A chord name moved by semitones (Dm7 by -4 is Bbm7)."""
    if not chord or not semis:
        return chord
    m = re.match(r"([A-G][#b]?)(.*)", chord)
    return NOTE_NAMES[(NOTE_NAMES.index(m.group(1)) + semis) % 12] + m.group(2) if m else chord


def sounding(key: dict, chords: list, cents: int) -> tuple[dict, list]:
    """The key and chords as they sound when the project's master pitch is off zero (written key kept in "written")."""
    semis = int(round(cents / 100.0))
    if not semis or not key.get("key"):
        return key, chords
    tonic = (key["tonic"] + semis) % 12
    return ({**key, "key": "%s %s" % (NOTE_NAMES[tonic], key["mode"]), "tonic": tonic, "written": key["key"], "master_pitch_cents": cents},
            [transpose_chord(c, semis) for c in chords])


def note_name(key: int) -> str:
    return "%s%d" % (NOTE_NAMES[key % 12], key // 12 - 1)


def roll(notes: list, start_bar: int, bars: int = 2, steps: int = 16, beats_per_bar: int = 4) -> list[str]:
    """A part's notes over a few bars as text, one line per bar: each 16th step shows the note (or chord as notes joined by '+') that
    starts there, '-' while a note holds, '.' for silence. start_bar counts from 1."""
    step = beats_per_bar / float(steps)
    lines = []
    for b in range(start_bar - 1, start_bar - 1 + bars):
        cells = ["."] * steps
        lo = b * beats_per_bar
        for n in notes:
            if lo - 4 <= n[0] < lo + beats_per_bar:
                k0 = int(round((n[0] - lo) / step))
                k1 = int(round((n[0] + n[3] - lo) / step))
                for k in range(max(0, k0 + 1), min(steps, k1)):
                    if cells[k] == ".":
                        cells[k] = "-"
                if 0 <= k0 < steps:
                    nm = note_name(n[2])
                    cells[k0] = nm if cells[k0] in (".", "-") else cells[k0] + "+" + nm
        lines.append(" ".join("%-3s" % c for c in cells))
    return lines


def busiest_bar(notes: list, beats_per_bar: int = 4) -> int:
    """The 1-based bar where a part first plays its most common bar shape (a fair sample of what it does)."""
    by: dict[int, list] = defaultdict(list)
    for n in notes:
        b = int(n[0] // beats_per_bar)
        by[b].append((round((n[0] - b * beats_per_bar) * 4) / 4.0, n[2] % 12))
    if not by:
        return 1
    shapes = Counter(tuple(sorted(v)) for v in by.values())
    top = shapes.most_common(1)[0][0]
    return min(b for b, v in by.items() if tuple(sorted(v)) == top) + 1


def presence(notes: list, audio_regs: list, sections: list, beats_per_bar: int = 4) -> list[int]:
    """For each section, how many bars of it the part plays in."""
    played = set()
    for n in notes:
        played.add(int(n[0] // beats_per_bar))
    for st, ln in audio_regs:
        for b in range(int(st // beats_per_bar), int(math.ceil((st + ln) / beats_per_bar))):
            played.add(b)
    return [sum(1 for b in range(s["start_bar"] - 1, s["start_bar"] - 1 + s["bars"]) if b in played) for s in sections]
