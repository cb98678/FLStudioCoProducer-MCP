"""Write the generated option files from the demo study: src/coproducer/data/options/kits.json (each demo's drum kit, sample paths as FL
writes them) and sound.json (the demos' instruments worth reusing: plugin, preset, register, where it plays, the channel to import, and,
when docs/demo_study/solo_measure.json is there, the measured sound and a Serum starting point). Run from the repo root:

    python tools/gen_demo_options.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
DATA = HOME / "docs" / "demo_study" / "data"
OPT = HOME / "src" / "coproducer" / "data" / "options"
MEASURED = HOME / "docs" / "demo_study" / "solo_measure.json"

# id: (song, channel names, role for the remix build, label, what, genres, moods)
SOUNDS = [
    ("sound.trance_lead_stack", "exoplanet", ["Main Lead 1", "Main Lead 1 #2", "Main Lead 1 #3", "Main Lead 1 #4", "Main Lead 1 #5", "Main Lead 1 #6", "Main Lead #6", "Main Lead #7"], "stab",
     "Trance lead stack (MiniSynth, Sytrus, Harmor on one part)", "Eight synths of three kinds playing the same gated chord line, each band-limited by its own filter, the filter velocity automated: width and weight from layering, not from one huge patch.",
     ["trance", "big_room", "edm"], ["euphoric", "epic", "anthemic"]),
    ("sound.sakura_pluck", "exoplanet", ["Pluck - Saku"], "arp", "Sakura string pluck", "A plucked physical-model string (Sakura) on a falling 16th arp: soft attack noise, short body, no synth fizz.",
     ["trance", "progressive_house", "melodic_techno", "future_garage"], ["dreamy", "nostalgic", "euphoric"]),
    ("sound.rolling_bass_layers", "exoplanet", ["B - Harmor", "B - 3xOsc", "B- Harm", "Default"], "bass", "Rolling bass in four layers",
     "Harmor, 3x Osc, Harmless and Sytrus on the same rolling 16ths into one bass bus (EQ, WaveShaper, Maximus, limiters, two filters): each layer covers one band.",
     ["trance", "psytrance", "techno"], ["driving", "euphoric"]),
    ("sound.pedal_arp_harmless", "exoplanet", ["Harmless #2"], "arp", "Harmless pedal arp", "A clean Harmless pluck on the pedal-tone arp, cutoff opened over long clips.",
     ["trance", "synthwave", "progressive_house"], ["uplifting", "driving"]),
    ("sound.wavvyy_poly", "future_house", ["Wavvyy Synth"], "stab", "Wavvyy poly synth (Harmless)", "A bright polyphonic Harmless patch playing chords as a 16th lead, pumped by an envelope controller.",
     ["future_house", "bass_house", "future_bass"], ["bouncy", "energetic", "party"]),
    ("sound.gms_future_bass", "future_house", ["FUTURE Bass"], "bass", "GMS future house bass", "GMS (Groove Machine Synth) mid bass with its own sub layer: the springy, filtered future house bass.",
     ["future_house", "bass_house", "g_house"], ["bouncy", "confident"]),
    ("sound.wasp_harmor_arp", "bien_duro", ["4.5.1 Wasp"], "arp", "Wasp arp (Harmor through Blood Overdrive and Flangus)", "A high Harmor arp driven and chorused into a buzzing 'wasp': a texture lead for latin and pop.",
     ["reggaeton", "pop", "latin"], ["playful", "hot", "sexy"]),
    ("sound.boobass_bounce", "bien_duro", ["5.1 Bass"], "bass", "BooBass bounce bass", "FL's BooBass (a modelled bass guitar) playing the dembow bounce, pumped by Gross Beat.",
     ["reggaeton", "funk", "nu_disco", "pop"], ["playful", "sexy", "party"]),
    ("sound.resonator_sytrus", "bien_duro", ["4.8 Resonator (Sytrus)"], "stab", "Resonator (Sytrus) with Mod X/Y moves", "A resonant Sytrus patch whose Mod X and Y are automated: a chord sound that keeps changing colour.",
     ["reggaeton", "pop", "electro"], ["mysterious", "sexy"]),
    ("sound.flex_simmering_pad", "bien_duro", ["4.9 Pad"], "stab", "FLEX pad (Olbaid Compendium)", "A FLEX pad preset under the chorus, low in the mix: air and width.",
     ["reggaeton", "pop", "rnb"], ["warm", "dreamy"]),
    ("sound.juno_bass", "right_night", ["Sytrus Juno Bass"], "bass", "Juno-style Sytrus bass", "A round Sytrus bass in the style of a Juno: square-ish, short, warm, sidechained gently.",
     ["pop_dance", "nu_disco", "synth_pop", "house"], ["happy", "romantic", "warm"]),
    ("sound.sytrus_brass", "right_night", ["Sytrus Brass"], "stab", "Sytrus brass stabs", "A synth brass on off-beat stabs: bright attack, short swell.",
     ["pop_dance", "nu_disco", "funk"], ["happy", "confident", "summer"]),
    ("sound.harmor_dark_pad", "right_night", ["Dark Pad"], "stab", "Harmor dark pad", "A slow, filtered Harmor pad that sits under a pop chorus without brightness.",
     ["pop_dance", "rnb", "deep_house"], ["romantic", "moody", "warm"]),
    ("sound.toxic_biohazard_arp", "im_awake", ["Toxic Biohazard"], "arp", "Toxic Biohazard high arp", "An FM/subtractive hybrid (Toxic Biohazard) on a high fast arp above the big room lead.",
     ["edm", "big_room", "electro_house"], ["euphoric", "energetic"]),
    ("sound.3xosc_lead_layers", "im_awake", ["3x Osc #16"], "stab", "3x Osc lead layers", "Seven 3x Osc channels on one Layer playing the lead: the simplest synth, stacked and detuned into a big room lead.",
     ["edm", "big_room", "electro_house"], ["anthemic", "euphoric", "party"]),
    ("sound.flex_driving_through", "time", ["Plucks 1"], "arp", "FLEX Driving Through pluck (Olbaid Compendium)", "A FLEX pluck, octave-doubled, on descending liquid arps; also the lead of the trap demo in a higher register.",
     ["liquid_dnb", "drum_and_bass", "trap", "future_bass"], ["soulful", "dreamy", "bittersweet"]),
    ("sound.dnb_sub_3xosc", "time", ["DNB SUB"], "sub", "3x Osc sine sub", "A plain 3x Osc sine sub held under the chords: the clean low end of liquid drum and bass.",
     ["drum_and_bass", "liquid_dnb", "halftime"], ["soulful", "melancholic"]),
    ("sound.synpluck_dual_arp", "africas_calling", ["Arp 01"], "arp", "FLEX Synpluck Dual arp (Mobile Synth Pluck)", "A FLEX pluck on the tresillo arp, its cutoff opened over 16 bars.",
     ["afro_house", "deep_house", "melodic_techno"], ["hypnotic", "tribal", "warm"]),
    ("sound.harmless_chord_pluck", "africas_calling", ["Chord Pluck"], "stab", "Harmless chord pluck", "Harmless chords with a short decay that is automated longer, then filtered by a Fruity Filter sweep.",
     ["afro_house", "house", "deep_house"], ["warm", "playful"]),
    ("sound.industrial_sytrus_bass", "night_terror", ["DEDZII TERROR"], "bass", "Distorted Sytrus 16th bass", "A Sytrus bass through Gross Beat and distortion playing the 16th ostinato: the mid layer of a four-layer industrial bass.",
     ["electro_industrial", "ebm", "industrial_techno"], ["dark", "aggressive", "menacing"]),
    ("sound.flex_808_flattened", "night_terror", ["808 Flattened"], "sub", "FLEX 808 Flattened", "A FLEX 808 preset used as the industrial bass's low layer.",
     ["electro_industrial", "trap", "drill"], ["dark", "menacing"]),
    ("sound.flex_crushspeak", "night_terror", ["Crushspeak Now"], "arp", "FLEX Crushspeak croak", "A talking, crushed FLEX preset whose high-pass and timbre are automated: a voice-like synth hook.",
     ["electro_industrial", "electro", "dubstep"], ["dark", "eerie", "aggressive"]),
    ("sound.kepler_pad", "song_for_you", ["Pads - Kepler"], "stab", "Kepler pad", "FL's Kepler (a dual-engine pad synth) on held chords, layered with DX10 and strings.",
     ["liquid_dnb", "trap", "ambient", "future_garage"], ["dreamy", "calm", "warm"]),
    ("sound.crusty_keys_vocoder", "song_for_you", ["Crusty Piano"], "stab", "Crusty FL Keys through a vocoder", "FL Keys made lo-fi and partly vocoded: a piano that sounds like a sample.",
     ["liquid_dnb", "lofi", "future_garage"], ["nostalgic", "dreamy"]),
    ("sound.dx10_pad", "song_for_you", ["Fruity DX10"], "stab", "DX10 FM pad", "DX10's two-operator FM as a glassy pad layer.",
     ["liquid_dnb", "afrobeats", "lofi"], ["dreamy", "calm"]),
    ("sound.synpluck_square", "song_for_you", ["Synpluck Square"], "arp", "FLEX Synpluck Square", "A square-wave FLEX pluck on the arp: hollow, retro.",
     ["liquid_dnb", "synthwave", "future_bass"], ["nostalgic", "playful"]),
    ("sound.heavy_808_sytrus", "inner_days_rework", ["Heavy 808"], "sub", "Sytrus heavy 808", "A long Sytrus 808 two octaves under the bass: the rework's new floor.",
     ["lofi", "hiphop", "trap"], ["warm", "cool"]),
    ("sound.harmor_octave_pluck", "inner_days_rework", ["Pluck"], "arp", "Harmor octave pluck", "Harmor playing octaves in a syncopated 16th figure: the rework's replacement for the vocal line.",
     ["lofi", "hiphop", "future_garage"], ["nostalgic", "melancholic"]),
    ("sound.cityscape_pad", "mic_check", ["Pad 1"], "stab", "FLEX Arksun Cityscape pad (Phasic Anomoly)", "A dark, phasing FLEX pad doubled by Harmless and FLEX strings: the drill bed.",
     ["uk_drill", "trap", "dark_techno"], ["dark", "cold", "menacing"]),
    ("sound.strung_space", "mic_check", ["Pad 3"], "stab", "FLEX Strung Space strings", "A FLEX string ensemble (Olbaid Compendium) an octave over the pad, through LuxeVerb.",
     ["uk_drill", "cinematic", "trap"], ["dark", "dramatic"]),
    ("sound.dx10_log_drum", "shine", ["Log Drum"], "bass", "DX10 log drum", "A short FM tom tuned as a bass (DX10): the log drum of afrobeats and amapiano.",
     ["afrobeats", "amapiano", "afro_house"], ["sunny", "playful", "warm"]),
    ("sound.synpluck_cube_pulse", "shine", ["Synpluck Cube"], "sub", "FLEX Synpluck Cube 8th pulse", "A plucked FLEX preset playing the bass's 8th pulse: a soft, rounded low end.",
     ["afrobeats", "afro_pop", "rnb"], ["sunny", "warm"]),
    ("sound.flex_brass_section", "shine", ["Brass Section 1"], "stab", "FLEX brass section (General Midi Library)", "Real-sounding brass from FLEX's GM library on off-beat stabs.",
     ["afrobeats", "pop", "funk"], ["happy", "confident"]),
    ("sound.ogun_chords", "madonna", ["High Chords"], "stab", "Ogun high chords", "Ogun (additive, metallic) on seventh-chord voicings, chorused and in a reverb: a glassy trip-hop chord.",
     ["trip_hop", "lounge", "downtempo"], ["moody", "mysterious", "sensual"]),
    ("sound.morphine_soft_pad", "madonna", ["Soft Pad"], "stab", "Morphine soft pad", "Morphine (additive) as a soft, breathing pad under the vocal.",
     ["trip_hop", "lounge", "ambient"], ["sensual", "calm", "moody"]),
    ("sound.harmor_blips", "madonna", ["Blips"], "arp", "Harmor chromatic blips", "Short Harmor blips on the falling chromatic line.",
     ["trip_hop", "soundtrack", "electro"], ["mysterious", "eerie", "playful"]),
    ("sound.flex_submarine", "never_out", ["Submarine"], "arp", "FLEX Submarine bounce", "A FLEX (Olbaid Compendium) bass-pluck on the octave bounce.",
     ["drum_and_bass", "electro", "synthwave"], ["driving", "energetic"]),
    ("sound.duck_stabs", "never_out", ["Lead Duck"], "stab", "Harmless duck stabs", "Short minor-triad stabs from Harmless, ducked hard.",
     ["drum_and_bass", "dubstep", "electro"], ["energetic", "dark"]),
    ("sound.flex_phoenix", "never_out", ["Phoenix"], "arp", "FLEX Phoenix lead (Arksun Cityscape)", "A FLEX lead whose master filter is opened by short clips: the drop's melody.",
     ["drum_and_bass", "melodic_dubstep", "trap"], ["epic", "melancholic"]),
    ("sound.flex_bas_lottunma", "with_you", ["BAS Lottunma"], "bass", "FLEX BAS Lottunma (Melodic Techno pack)", "The melodic techno 16th bass: FLEX preset with its cutoff and release automated, a Harmor sub under it.",
     ["melodic_techno", "techno", "progressive_house"], ["hypnotic", "dark", "driving"]),
    ("sound.flex_plk_navid", "with_you", ["PLK Navid"], "arp", "FLEX PLK Navid (Melodic Techno pack)", "The sequence pluck of melodic techno: short, resonant, with Space and TuneX macros moving.",
     ["melodic_techno", "techno", "afro_house"], ["hypnotic", "dreamy", "melancholic"]),
    ("sound.sytrus_mtechno_pad", "with_you", ["Synth Pad "], "stab", "Sytrus five-note pad", "A wide Sytrus pad playing five-note voicings with its filter automated.",
     ["melodic_techno", "progressive_house", "trance"], ["dreamy", "melancholic"]),
    ("sound.tinke_bell", "thief", ["Tinke Bell"], "arp", "FLEX Tinke Bell (General Midi Library)", "A music-box bell on the octave-doubled future bass arp.",
     ["future_bass", "pop", "melodic_dubstep"], ["magical", "euphoric", "bittersweet"]),
    ("sound.saw_bass_gated", "thief", ["Saw Bass"], "bass", "3x Osc saw bass through Gross Beat", "A raw 3x Osc saw bass gated by Gross Beat: the future bass drop's growl.",
     ["future_bass", "trap", "melodic_dubstep"], ["euphoric", "energetic"]),
    ("sound.overdrive_sytrus_arp", "use_me", ["Synth Arp"], "arp", "Sytrus arp through Blood Overdrive and Love Philter", "A Sytrus arp driven, reverbed and filtered by Love Philter, ending in Effector: the afrobeats hook arp.",
     ["afrobeats", "afro_pop", "dancehall"], ["sunny", "romantic", "dreamy"]),
    ("sound.flex_808_clean", "stroll_up", ["808 Clean"], "sub", "FLEX 808 Clean (Mobile Tuned 808 Bass)", "A clean tuned 808 from FLEX, long and mono.",
     ["trap", "drill", "hiphop"], ["dark", "cool"]),
    ("sound.fl_keys_bells", "stroll_up", ["FL Keys"], "stab", "FL Keys staccato bells", "FL Keys high and short: a bell-like keys ostinato.",
     ["trap", "drill", "hiphop"], ["dark", "eerie", "cool"]),
    ("sound.creeper_drone", "stroll_up", ["Creeper Drone"], "stab", "FLEX Creeper Drone (Arksun Cityscape)", "A low FLEX drone through WaveShaper, Hyper Chorus, Love Philter and Spreader: a dark trap bed.",
     ["trap", "drill", "dark_techno"], ["dark", "menacing", "moody"]),
    ("sound.directwave_rhodes", "secret_agent", ["Rhodes"], "stab", "DirectWave Rhodes", "A sampled Rhodes (DirectWave) voicing the spy chord.",
     ["soundtrack", "jazz", "lofi", "trip_hop"], ["mysterious", "nostalgic", "warm"]),
    ("sound.harmor_forest_bass", "secret_agent", ["Forest"], "bass", "Harmor 'Forest' 16th bass", "A Harmor bass repeating one note in 16ths under the cue: tension by repetition.",
     ["soundtrack", "cinematic", "electro"], ["tense", "suspense"]),
    ("sound.wave_traveller_lead", "secret_agent", ["Wave Traveller #3"], "arp", "Wave Traveller lead", "A Wave Traveller (scratch-able sample player) lead line.",
     ["soundtrack", "hiphop", "trip_hop"], ["playful", "mysterious"]),
]


GENRES = {"Future House": ["future_house", "house", "bass_house"], "Reggaeton": ["reggaeton", "latin", "moombahton"], "Pop Dance": ["pop_dance", "nu_disco", "house"],
          "EDM": ["edm", "big_room", "electro_house"], "D&B": ["drum_and_bass", "liquid_dnb", "dnb"], "Drum & Bass": ["drum_and_bass", "dnb", "liquid_dnb"],
          "Afro House": ["afro_house", "deep_house", "organic_house"], "Electro Industrial": ["electro_industrial", "industrial_techno", "ebm"],
          "Lo-Fi": ["lofi", "chillhop", "hiphop"], "Trance": ["trance", "progressive_house"], "UK Drill": ["uk_drill", "drill", "grime"],
          "Afrobeats": ["afrobeats", "afro_pop", "amapiano"], "Trip Hop/ Lounge": ["trip_hop", "downtempo", "lounge"], "Melodic Techno": ["melodic_techno", "techno"],
          "Future Bass": ["future_bass", "melodic_dubstep"], "Trap": ["trap", "hiphop"], "Soundtrack": ["soundtrack", "cinematic", "spy"]}


def same_song(a: str, b: str) -> bool:
    """Render copies and study files name a song slightly differently (an accent dropped, a name cut at 60 characters)."""
    def n(x):
        return "".join(c for c in x.lower() if c.isalnum())
    na, nb = n(a), n(b)
    k = min(len(na), len(nb))
    return bool(na) and (na == nb or (k >= 16 and na[:k] == nb[:k]))   # a short title (LeriQ SHINE) matches in full


def load_song(sid: str, sources: dict) -> dict:
    return json.loads((DATA / (sources[sid]["data"] + ".json")).read_text(encoding="utf-8"))


def kits(sources: dict) -> dict:
    out = [{"id": "kit.synth", "label": "Synthesized one-shots (the coproducer's own kit)",
            "what": "The kit oneshots.py synthesizes for every remix: neutral, always available, the fallback when no demo kit fits the genre.",
            "genres": ["*"], "moods": [], "energy": "any", "sources": [], "engine": {"voices": {}}}]
    for sid, src in sources.items():
        d = load_song(sid, sources)
        voices = {}
        for v, rows in d["kit"].items():
            if rows:
                voices[v] = rows[0]["sample"]
        if not voices:
            continue
        out.append({"id": "kit.%s" % sid, "label": "%s kit (%s)" % (src["title"].split("(")[0].strip(), src["genre"]),
                    "what": "The drum samples %s uses, voice by voice (the most played sample of each voice). FL's factory paths: on this machine they resolve under the FL install's Data folder." % src["artists"],
                    "genres": GENRES.get(src["genre"], [src["genre"].lower().replace(" ", "_")]), "moods": [], "energy": "any",
                    "sources": [{"song": sid, "where": "drum channels"}],
                    "engine": {"voices": voices, "alternates": {v: [r["sample"] for r in rows[1:]] for v, rows in d["kit"].items() if len(rows) > 1}}})
    return {"category": "kit", "what": "Drum kits: one per demo song, the samples it really plays. engine.voices maps a kit voice (kick, snare, clap, hat, ohat, shaker, rim, tom, crash, perc, ride) to a sample path as FL stores it (%FLStudioFactoryData% is the FL install folder); the remix build resolves the path on the host and uses it in place of the synthesized one-shot.",
            "options": out}


def sound_options(sources: dict, measured: dict) -> dict:
    out = []
    for sid_, song, names, role, label, what, genres, moods in SOUNDS:
        d = load_song(song, sources)
        parts = [p for p in d["parts"] if (p["name"] or "") in names]
        if not parts:
            print("not found:", sid_, song, names)
            continue
        lead = max(parts, key=lambda p: p["notes"])
        row = {"id": sid_, "label": label, "what": what, "genres": genres, "moods": moods, "energy": "any",
               "sources": [{"song": song, "where": ", ".join(names)}],
               "plugin": sorted({p["plugin"] or "sampler" for p in parts}), "preset": lead.get("preset"), "chain": lead.get("chain"),
               "register": lead.get("range"), "polyphony": lead.get("polyphony"),
               "engine": {"role": role, "import": {"song": song, "flp": sources[song]["data"], "channels": [p["channel"] for p in parts], "names": [p["name"] for p in parts]}}}
        m = next((v for k, v in measured.items() if same_song(v.get("song", ""), sources[song]["data"]) and set(v.get("names") or [v.get("name")]) & set(names)
                  and not v.get("silent") and (v.get("peak_db") if v.get("peak_db") is not None else -999) > -45), None)   # a near-silent solo measures noise, not the sound
        if m and m.get("describe", {}).get("notes"):
            ds = m["describe"]
            row["measured"] = {k: ds.get(k) for k in ("attack_s", "decay_s", "sustain", "release_s", "centroid_hz", "rolloff_hz", "flatness", "gated_share", "register", "width", "shape", "words")}
            if m.get("serum_start"):
                row["serum_start"] = m["serum_start"]
        out.append(row)
    return {"category": "sound", "what": "Instruments from the demos to reuse: engine.import names the channel(s) of the demo project (its sandbox render copy) that the remix build can import as the part's instrument (role: stab, arp, sub or bass), with the patch exactly as the demo's designer left it. measured is the solo render read by soundbrief.describe; serum_start is soundbrief's Serum 2 starting point for the same sound, for when the part should be a generated Serum sound in this sound's direction.",
            "options": out}


def main() -> int:
    sources = json.loads((OPT / "sources.json").read_text(encoding="utf-8"))["songs"]
    measured = json.loads(MEASURED.read_text(encoding="utf-8")) if MEASURED.is_file() else {}
    (OPT / "kits.json").write_text(json.dumps(kits(sources), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (OPT / "sound.json").write_text(json.dumps(sound_options(sources, measured), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("kits and sounds written", "(with measurements)" if measured else "(no solo measurements yet)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
