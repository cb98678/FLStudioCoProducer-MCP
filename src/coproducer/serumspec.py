"""serum-mcp PresetSpec parts for sounds made from a song's own material (skill serum-wavetables, 2026-10-28).

Each move returns a part (envelopes, LFOs, mod routes, effects, macros by index) and assemble() merges parts into one PresetSpec dict for
generate_preset. Indices are serum-mcp's, 0-based: Env 1 is env0 (the amp envelope), Env 2 is env1, LFO 1 is lfo0, Macro 1 is macro0,
Osc A is oscillator0, Filter 1 is filter0; an effect is addressed by its place in fx_chain (fx0.wet). Only destinations serum-mcp lists
as confirmed are used (preset/schema.py MOD_DEST_TARGETS, commit eada85a): oscillator volume, pitch and table position, filter cutoff,
envelope times, an effect's wet and FXUtils level_out. A distortion's drive and a compressor's gain are not mod destinations there, so
the dirt and duck moves work through the effect's wet.

LFO timing: an LFO whose rate is left unset runs at Serum's default, a quarter note synced to the tempo (serum-mcp, confirmed in Serum).
A 16th or 8th chop is drawn as four or two on-off steps inside that quarter note rather than by a rate value, because serum-mcp has no
confirmed rate value for 1/16. Retrig mode restarts it on every note, so it lines up when the notes start on the grid.
"""
from __future__ import annotations

import copy


def amp(attack_s: float = 0.001, decay_s: float = 1.0, sustain: float = 1.0, release_s: float = 0.05, hold_s: float = 0.0) -> dict:
    """The amp envelope (env0)."""
    return {"envelopes": {0: {"attack": attack_s, "hold": hold_s, "decay": decay_s, "sustain": sustain, "release": release_s}}}


def pluck(attack_s: float = 0.001, decay_s: float = 0.22, depth: float = 45.0, env: int = 1, filt: int = 0, macro: int | None = 0) -> dict:
    """Env 2 (env1) on the filter cutoff: a fast attack and a short decay to nothing, so each note bites and closes (a percussive pluck).
    With macro set, that macro scales the envelope's depth (Serum's aux source: amount times the macro's value)."""
    route = {"source": "env%d" % env, "destination": "filter%d.cutoff" % filt, "amount": depth}
    if macro is not None:
        route["aux_source"] = "macro%d" % macro
    return {"envelopes": {env: {"attack": attack_s, "hold": 0.0, "decay": decay_s, "sustain": 0.0, "release": decay_s}}, "mod_routes": [route]}


def _steps(n: int, on_first: bool = True) -> list[dict]:
    """A square LFO curve with n on-off cycles across the LFO's cycle: high (1) while sounding, low (0) while gated."""
    pts, eps = [], 0.002
    for k in range(n):
        a, mid = k / n, (k + 0.5) / n
        hi, lo = (1.0, 0.0) if on_first else (0.0, 1.0)
        pts += [{"x": round(a + (eps if k else 0.0), 4), "y": hi}, {"x": round(mid - eps, 4), "y": hi}, {"x": round(mid, 4), "y": lo},
                {"x": round((k + 1) / n - eps, 4), "y": lo}]
    pts.append({"x": 1.0, "y": pts[0]["y"]})
    return pts


def chop(division: int = 16, lfo: int = 0, target: str = "oscillator0.volume", depth: float = -100.0) -> dict:
    """A gate on every 16th (or 8th): LFO steps that pull the target down for the second half of each step. On a sampled vocal or a
    held chord this is the chopped house gate; on oscillator pitch with a small depth it is a stepped trill instead."""
    if division not in (4, 8, 16, 32):
        raise ValueError("division is 4, 8, 16 or 32")
    lfo_spec = {"mode": "Retrig", "curve": _steps(division // 4, on_first=False)}
    return {"lfos": {lfo: lfo_spec}, "mod_routes": [{"source": "lfo%d" % lfo, "destination": target, "amount": depth}]}


def duck(fx_index: int, lfo: int = 1, depth: float = -50.0, recover: float = 0.35) -> dict:
    """The space ducks on every beat and swells back (an inverted sidechain inside the synth): a spike at the start of each quarter note
    that falls off by `recover` of the beat, routed negative into an effect's wet. It follows the tempo, not the kick: it lines up on a
    four-on-the-floor kick when the notes start on the beat. FL's own sidechain from the kick (mix-engineer) is the exact one."""
    curve = [{"x": 0.0, "y": 1.0}, {"x": round(recover, 3), "y": 0.12, "tension": 0.3}, {"x": 1.0, "y": 0.0}]
    return {"lfos": {lfo: {"mode": "Retrig", "curve": curve}},
            "mod_routes": [{"source": "lfo%d" % lfo, "destination": "fx%d.wet" % fx_index, "amount": depth}]}


def macros(table_osc: int | None = 0, table_amount: float = 60.0, decay_env: int | None = 1, decay_amount: float = 40.0,
           room_fx: int | None = None, room_amount: float = 30.0, dirt_fx: int | None = None, dirt_amount: float = 60.0) -> dict:
    """Four performance macros: 1 GRIP (table position, and the pluck depth through pluck's aux), 2 SNAP (Env 2's decay), 3 ROOM (the
    reverb's wet, up to room_amount), 4 DIRT (the distortion's wet). Set an index to None to leave that macro out."""
    names, routes = {}, []
    for k, (name, on, dest, amt) in enumerate((("GRIP", table_osc, "oscillator%s.table_position", table_amount),
                                               ("SNAP", decay_env, "env%s.decay", decay_amount),
                                               ("ROOM", room_fx, "fx%s.wet", room_amount), ("DIRT", dirt_fx, "fx%s.wet", dirt_amount))):
        if on is None:
            continue
        names[k] = {"name": name, "value": 0.0}
        routes.append({"source": "macro%d" % k, "destination": dest % on, "amount": amt})
    return {"macros": names, "mod_routes": routes}


def room(size: float = 20.0, wet: float = 0.0, kind: str = "kHall") -> dict:
    """A small reverb (size 20 %) whose wet a macro raises; wet 0 so it is dry until the macro moves."""
    return {"fx": [{"type": "FXReverb", "wet": wet, "params": {"kParamType": kind, "kParamSize": size}}]}


def dirt(mode: str = "kTapeSat", drive: float = 45.0, wet: float = 0.0) -> dict:
    """A distortion at a fixed drive whose wet a macro raises. Serum 2 has no mode called Tube: the saturating modes are kTapeSat,
    kSoftSat, kOverdrive and kStompBox; kDiode1 and kDiode2 are the diode clippers (serum-mcp's FX_PARAMS, commit eada85a)."""
    return {"fx": [{"type": "FXDistortion", "wet": wet, "params": {"kParamMode": mode, "kParamDrive": drive}}]}


def assemble(name: str, description: str, oscillators: list[dict], filters: list[dict] | None = None, parts: list[dict] | None = None,
             amp_env: dict | None = None, master_volume: float = 0.5) -> dict:
    """One PresetSpec from oscillators, filters and parts. Envelope and LFO slots below the highest used are filled (serum-mcp writes
    lists by position); effects are concatenated in the order of the parts, so a part's fx index is known before routing to it (use
    fx_index_after to get it)."""
    envs, lfos, mac, routes, fx = {}, {}, {}, [], []
    for p in ([amp_env] if amp_env else []) + list(parts or []):
        p = copy.deepcopy(p)
        envs.update(p.get("envelopes", {}))
        lfos.update(p.get("lfos", {}))
        mac.update(p.get("macros", {}))
        routes += p.get("mod_routes", [])
        fx += p.get("fx", [])
    envs.setdefault(0, amp()["envelopes"][0])
    spec = {"name": name, "description": description, "oscillators": oscillators, "filters": filters or [],
            "envelopes": [envs.get(i, {}) for i in range(max(envs) + 1)], "global": {"master_volume": master_volume}}
    if lfos:
        spec["lfos"] = [lfos.get(i, {}) for i in range(max(lfos) + 1)]
    if mac:
        spec["macros"] = [mac.get(i, {"name": "", "value": 0.0}) for i in range(max(mac) + 1)]
    if routes:
        spec["mod_routes"] = routes
    if fx:
        spec["fx_chain"] = fx
    return spec


def fx_index_after(parts: list[dict], kind: str) -> int | None:
    """The fx_chain index the first effect of type kind (FXReverb, FXDistortion) gets when parts are assembled in this order."""
    i = 0
    for p in parts:
        for f in p.get("fx", []):
            if f["type"] == kind:
                return i
            i += 1
    return None


def table_osc(path: str, frames: int, octave: float = 0.0, volume: float = 0.75, unison: float = 1.0, detune: float = 0.0) -> dict:
    """Osc settings for a table made by make_wavetable: serum-mcp's sample_source slices it into exactly its own frames (the file is
    frames times 2048 samples at 44.1 kHz, so the evenly spaced slices fall on the frame starts)."""
    return {"sample_source": path, "sample_frames": int(frames), "octave": octave, "volume": volume, "unison": unison, "detune": detune}


def table_ref(relative: str, octave: float = 0.0, volume: float = 0.75, unison: float = 1.0, detune: float = 0.0) -> dict:
    """Osc settings for a table already in Serum's Tables folder (relative to it, forward slashes, e.g. User/sandbox/song/bass.wav):
    serum-mcp resolves a non-curated wavetable name as a path under Tables and reads its frame count from the file. Serum plays the
    frames exactly as written, with no edge fade."""
    return {"wavetable": relative.replace("\\", "/").lstrip("/"), "octave": octave, "volume": volume, "unison": unison, "detune": detune}
