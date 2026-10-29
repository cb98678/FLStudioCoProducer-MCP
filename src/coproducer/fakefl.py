"""In-memory FL Studio scripting API for tests (the fake FL harness).

Same function names and argument shapes as the official reference for the curated set, with a call log
and fault injection: ignore_writes (FL's silent-ignore behavior), api_level (hide newer functions).
It is generated-adjacent: the set of functions and their `since` levels come from data/api_inventory.json.
"""
from __future__ import annotations

import ast
import copy
import inspect
import json
import sys
import types
from pathlib import Path
from typing import Any, Callable

MODULES = ("transport", "mixer", "channels", "patterns", "plugins", "playlist",
           "arrangement", "general", "ui", "device", "midi")


def _inventory() -> dict:
    with open(Path(__file__).resolve().parent / "data" / "api_inventory.json", "r", encoding="utf-8") as f:
        return json.load(f)


_FADER_POINTS = ((0.0, -120.0), (0.25, -19.05), (0.5, -9.18), (0.8, 0.0), (1.0, 5.59))      # measured on FL 26.1.7, see docs/FL_API_FINDINGS.md


def measured_fader_db(v: float) -> float:
    """Fader position 0..1 to dB by straight lines between the measured points."""
    v = min(1.0, max(0.0, v))
    for (v0, d0), (v1, d1) in zip(_FADER_POINTS, _FADER_POINTS[1:]):
        if v <= v1:
            return d0 + (d1 - d0) * (v - v0) / (v1 - v0)
    return _FADER_POINTS[-1][1]


class FakeFL:
    def __init__(self, tracks: int = 6, channels: int = 3, patterns: int = 4, api_level: int = 45,
                 ignore_writes: bool = False) -> None:
        self.api_level = api_level
        self.swing = 0.0
        self.db_law: Callable[[float], float] = measured_fader_db
        self.ignore_writes = ignore_writes
        self.log: list[tuple[str, str, tuple]] = []
        self.mixer = [{"name": "Master" if i == 0 else f"Insert {i}", "volume": 0.8, "pan": 0.0, "stereo": 0.0,
                       "mute": False, "solo": False, "color": 0, "src": 0.0,
                       "eq": [{"gain": 0.5, "freq": 0.5, "bw": 0.5} for _ in range(3)],
                       "routes": {0: 0.8} if i else {}} for i in range(tracks)]
        self.channels = [{"name": f"Channel {i}", "volume": 0.78, "pan": 0.0, "mute": False, "solo": False,
                          "color": 0, "target": 0, "type": 0} for i in range(channels)]
        self.patterns = {i + 1: {"name": f"Pattern {i + 1}", "length": 64} for i in range(patterns)}
        self.pattern_current = 1
        self.pattern_selected: set[int] = {1}
        self.plugins: dict[tuple[int, int], dict] = {
            (0, -1): {"name": "Fake Synth", "color": 0,
                      "params": [[n, 0.5] for n in ("Cutoff", "Resonance", "Drive", "Attack", "Release", "Mix", "", "")]},
            (1, 0): {"name": "Fake EQ", "color": 0, "params": [["Low", 0.5], ["Mid", 0.5], ["High", 0.5]]},
        }
        self.transport = {"playing": False, "recording": False, "loop": 0, "pos": 0.0}
        self.playlist = [{"name": f"Track {i + 1}", "mute": False, "solo": False, "color": 0} for i in range(5)]
        self.markers: list[tuple[int, str]] = []
        self.title = "fake_project"
        self.changed = 0
        self.undos: list[str] = []
        self._history: list[tuple] = []
        self.outbox: list[bytes] = []
        self.tempo = 140.0
        self.windows: dict[int, bool] = {}
        self._inv = _inventory()
        self.modules = self._build()

    # ------------------------------------------------------------------ helpers
    def calls(self, module: str, func: str) -> list[tuple]:
        return [a for m, f, a in self.log if m == module and f == func]

    def gain(self, i: int) -> float:
        return self.mixer[i]["volume"] / 0.8

    ASSUMED: tuple = ()  # names the fake has that neither the stubs nor the observed overlay list

    def _since(self, module: str, func: str) -> int:
        return int(self._inv.get(f"{module}.{func}", {}).get("since", 1))

    def _write(self, module: str, func: str, args: tuple, apply: Callable[[], Any]) -> None:
        self.log.append((module, func, args))
        if not self.ignore_writes:
            self._history.append(self._state())
            apply()
            self.changed = 1

    def _state(self) -> tuple:
        return copy.deepcopy((self.mixer, self.channels, self.patterns, self.plugins, self.playlist,
                              self.markers, self.tempo, self.transport, self.pattern_current))

    def _restore(self, state: tuple) -> None:
        mixer, channels, patterns, plugins, playlist, markers, tempo, transport, current = copy.deepcopy(state)
        self.mixer[:] = mixer
        self.channels[:] = channels
        self.playlist[:] = playlist
        self.markers[:] = markers
        for target, source in ((self.patterns, patterns), (self.plugins, plugins), (self.transport, transport)):
            target.clear()
            target.update(source)
        self.tempo, self.pattern_current = tempo, current

    def _read(self, module: str, func: str, args: tuple, value: Callable[[], Any]) -> Any:
        self.log.append((module, func, args))
        return value()

    @staticmethod
    def _idx(seq: Any, i: int, base: int = 0) -> Any:
        if type(i) is not int or i < base or i - base >= len(seq):
            raise IndexError(f"index {i} out of range")
        return seq[i - base]

    # ------------------------------------------------------------------ the API
    def _functions(self) -> dict[str, dict[str, Callable]]:
        S, R, W = self, self._read, self._write
        mx, ch, pl = S.mixer, S.channels, S.playlist
        T = S.transport

        def tog(cur: bool, value: int) -> bool:
            return (not cur) if value == -1 else bool(value)

        def track(i): return S._idx(mx, i)
        def chan(i): return S._idx(ch, i)
        def eq(i, band): return S._idx(S._idx(mx, i)["eq"], band)
        def plug(index, slot):
            p = S.plugins.get((index, slot))
            if p is None:
                raise IndexError("no plugin there")
            return p
        def param(index, slot, pi): return S._idx(plug(index, slot)["params"], pi)

        def set_(d, k, v): d[k] = v

        def set_tempo(milli):
            if type(milli) is not int or not 10000 <= milli <= 522000:
                raise RuntimeError("Range error")
            S.tempo = milli / 1000.0

        def pat(i): return S.patterns[i]

        def pat_length(i, n):
            if type(n) is not int or n < 1:
                raise RuntimeError("Range error")
            pat(i)["length"] = n

        def pat_clear(i):
            pat(i)["notes"] = []

        def solo_track(i, value=-1, mode=-1):
            t = track(i); t["solo"] = tog(t["solo"], value)
        def mute_play(i, value=-1):
            t = S._idx(pl, i, 1); t["mute"] = tog(t["mute"], value)

        def set_route(i, d, v, ui=False):
            track(d)
            t = track(i)
            if v: t["routes"].setdefault(d, 0.8)
            else: t["routes"].pop(d, None)

        def peak(i, mode):
            t = track(i)
            return min(t["src"] * 10 ** (S.db_law(t["volume"]) / 20), 1.5)

        def vol_get(i, mode=0):
            v = track(i)["volume"]
            return S.db_law(v) if mode == 1 else v

        def route_level_set(i, d, level):
            t = track(i)
            if d not in t["routes"]: raise IndexError("no route")
            t["routes"][d] = level

        def route_level_get(i, d):
            t = track(i)
            if d not in t["routes"]: raise IndexError("no route")
            return t["routes"][d]

        def tr_start():
            T["playing"] = not T["playing"]
        def tr_stop():
            T["playing"] = False; T["pos"] = 0.0
        def tr_loop():
            T["loop"] = 0 if T["loop"] else 1

        def marker_add(time, name):
            S.markers.append((time, name))

        def undo():
            S.log.append(("general", "undo", ()))
            if S.ignore_writes or not S._history:
                return 0
            S._restore(S._history.pop())
            return 1

        return {
            "transport": {
                "start": lambda: W("transport", "start", (), tr_start),
                "stop": lambda: W("transport", "stop", (), tr_stop),
                "record": lambda: W("transport", "record", (), lambda: set_(T, "recording", not T["recording"])),
                "isPlaying": lambda: R("transport", "isPlaying", (), lambda: T["playing"]),
                "isRecording": lambda: R("transport", "isRecording", (), lambda: T["recording"]),
                "getLoopMode": lambda: R("transport", "getLoopMode", (), lambda: T["loop"]),
                "setLoopMode": lambda: W("transport", "setLoopMode", (), tr_loop),
                "getSongPos": lambda mode=-1: R("transport", "getSongPos", (mode,), lambda: T["pos"]),
                "setSongPos": lambda position, mode=-1: W("transport", "setSongPos", (position, mode), lambda: set_(T, "pos", position)),
                "getSongLength": lambda mode: R("transport", "getSongLength", (mode,), lambda: 3840),
            },
            "mixer": {
                "trackCount": lambda: R("mixer", "trackCount", (), lambda: len(mx)),
                "getTrackName": lambda index: R("mixer", "getTrackName", (index,), lambda: track(index)["name"]),
                "setTrackName": lambda index, name: W("mixer", "setTrackName", (index, name), lambda: set_(track(index), "name", name)),
                "getTrackVolume": lambda index, mode=0: R("mixer", "getTrackVolume", (index, mode), lambda: vol_get(index, mode)),
                "setTrackVolume": lambda index, volume, pickupMode=0: W("mixer", "setTrackVolume", (index, volume, pickupMode), lambda: set_(track(index), "volume", float(volume))),
                "getTrackPan": lambda index: R("mixer", "getTrackPan", (index,), lambda: track(index)["pan"]),
                "setTrackPan": lambda index, pan, pickupMode=0: W("mixer", "setTrackPan", (index, pan, pickupMode), lambda: set_(track(index), "pan", float(pan))),
                "getTrackStereoSep": lambda index: R("mixer", "getTrackStereoSep", (index,), lambda: track(index)["stereo"]),
                "setTrackStereoSep": lambda index, pan, pickupMode=0: W("mixer", "setTrackStereoSep", (index, pan, pickupMode), lambda: set_(track(index), "stereo", float(pan))),
                "isTrackMuted": lambda index: R("mixer", "isTrackMuted", (index,), lambda: track(index)["mute"]),
                "muteTrack": lambda index, value=-1: W("mixer", "muteTrack", (index, value), lambda: set_(track(index), "mute", tog(track(index)["mute"], value))),
                "isTrackSolo": lambda index: R("mixer", "isTrackSolo", (index,), lambda: track(index)["solo"]),
                "soloTrack": lambda index, value=-1, mode=-1: W("mixer", "soloTrack", (index, value, mode), lambda: solo_track(index, value, mode)),
                "getTrackPeaks": lambda index, mode: R("mixer", "getTrackPeaks", (index, mode), lambda: peak(index, mode)),
                "getTrackColor": lambda index: R("mixer", "getTrackColor", (index,), lambda: track(index)["color"]),
                "setTrackColor": lambda index, color: W("mixer", "setTrackColor", (index, color), lambda: set_(track(index), "color", color)),
                "getRouteToLevel": lambda index, destIndex: R("mixer", "getRouteToLevel", (index, destIndex), lambda: route_level_get(index, destIndex)),
                "setRouteToLevel": lambda index, destIndex, level: W("mixer", "setRouteToLevel", (index, destIndex, level), lambda: route_level_set(index, destIndex, level)),
                "setRouteTo": lambda index, destIndex, value, updateUI=False: W("mixer", "setRouteTo", (index, destIndex, value, updateUI), lambda: set_route(index, destIndex, value, updateUI)),
                "getRouteSendActive": lambda index, destIndex: R("mixer", "getRouteSendActive", (index, destIndex), lambda: destIndex in track(index)["routes"]),
                "getPluginMuteState": lambda index, slotIndex: R("mixer", "getPluginMuteState", (index, slotIndex), lambda: int(plug(index, slotIndex).get("mute", 1))),
                "setPluginMuteState": lambda index, slotIndex, value: W("mixer", "setPluginMuteState", (index, slotIndex, value), lambda: plug(index, slotIndex).__setitem__("mute", int(value))),
                "getPluginMixLevel": lambda index, slotIndex: R("mixer", "getPluginMixLevel", (index, slotIndex), lambda: float(plug(index, slotIndex).get("mix", 1.0))),
                "setPluginMixLevel": lambda index, slotIndex, value: W("mixer", "setPluginMixLevel", (index, slotIndex, value), lambda: plug(index, slotIndex).__setitem__("mix", float(value))),
                "getEqGain": lambda index, band, mode=0: R("mixer", "getEqGain", (index, band, mode), lambda: eq(index, band)["gain"]),
                "setEqGain": lambda index, band, value: W("mixer", "setEqGain", (index, band, value), lambda: set_(eq(index, band), "gain", value)),
                "getEqFrequency": lambda index, band, mode=0: R("mixer", "getEqFrequency", (index, band, mode), lambda: eq(index, band)["freq"]),
                "setEqFrequency": lambda index, band, value: W("mixer", "setEqFrequency", (index, band, value), lambda: set_(eq(index, band), "freq", value)),
                "getEqBandwidth": lambda index, band: R("mixer", "getEqBandwidth", (index, band), lambda: eq(index, band)["bw"]),
                "setEqBandwidth": lambda index, band, value: W("mixer", "setEqBandwidth", (index, band, value), lambda: set_(eq(index, band), "bw", value)),
                # Measured on FL 26.1.7: the flag is the reverse of the stub text. asInt=True gives BPM as a float,
                # the default gives milli-BPM as an integer. The setter takes milli-BPM and raises "Range error" otherwise.
                "getCurrentTempo": lambda asInt=False: R("mixer", "getCurrentTempo", (asInt,), lambda: float(S.tempo) if asInt else int(round(S.tempo * 1000))),
                "setCurrentTempo": lambda tempo: W("mixer", "setCurrentTempo", (tempo,), lambda: set_tempo(tempo)),
                "isTrackArmed": lambda index: R("mixer", "isTrackArmed", (index,), lambda: (track(index), False)[1]),
            },
            "channels": {
                "channelCount": lambda globalCount=False: R("channels", "channelCount", (globalCount,), lambda: len(ch)),
                "getChannelName": lambda index, useGlobalIndex=False: R("channels", "getChannelName", (index,), lambda: chan(index)["name"]),
                "setChannelName": lambda index, name, useGlobalIndex=False: W("channels", "setChannelName", (index, name), lambda: set_(chan(index), "name", name)),
                "getChannelVolume": lambda index, mode=False, useGlobalIndex=False: R("channels", "getChannelVolume", (index, mode), lambda: chan(index)["volume"]),
                "setChannelVolume": lambda index, volume, pickupMode=0, useGlobalIndex=False: W("channels", "setChannelVolume", (index, volume), lambda: set_(chan(index), "volume", float(volume))),
                "getChannelPan": lambda index, useGlobalIndex=False: R("channels", "getChannelPan", (index,), lambda: chan(index)["pan"]),
                "setChannelPan": lambda index, pan, pickupMode=0, useGlobalIndex=False: W("channels", "setChannelPan", (index, pan), lambda: set_(chan(index), "pan", float(pan))),
                "isChannelMuted": lambda index, useGlobalIndex=False: R("channels", "isChannelMuted", (index,), lambda: chan(index)["mute"]),
                "muteChannel": lambda index, value=-1, useGlobalIndex=False: W("channels", "muteChannel", (index, value), lambda: set_(chan(index), "mute", tog(chan(index)["mute"], value))),
                "isChannelSolo": lambda index, useGlobalIndex=False: R("channels", "isChannelSolo", (index,), lambda: chan(index)["solo"]),
                "soloChannel": lambda index, useGlobalIndex=False: W("channels", "soloChannel", (index,), lambda: set_(chan(index), "solo", not chan(index)["solo"])),
                "getChannelColor": lambda index, useGlobalIndex=False: R("channels", "getChannelColor", (index,), lambda: chan(index)["color"]),
                "setChannelColor": lambda index, color, useGlobalIndex=False: W("channels", "setChannelColor", (index, color), lambda: set_(chan(index), "color", color)),
                "getTargetFxTrack": lambda index, useGlobalIndex=False: R("channels", "getTargetFxTrack", (index,), lambda: chan(index)["target"]),
                "setTargetFxTrack": lambda channelIndex, mixerIndex, useGlobalIndex=False: W("channels", "setTargetFxTrack", (channelIndex, mixerIndex), lambda: (track(mixerIndex), set_(chan(channelIndex), "target", mixerIndex))),
                "getChannelType": lambda index, useGlobalIndex=False: R("channels", "getChannelType", (index,), lambda: chan(index)["type"]),
                "selectOneChannel": lambda index, useGlobalIndex=False: W("channels", "selectOneChannel", (index,), lambda: chan(index)),
                "getSwing": lambda: R("channels", "getSwing", (), lambda: S.swing),
                "setSwing": lambda value: W("channels", "setSwing", (value,), lambda: set_(S.__dict__, "swing", float(value))),
                "midiNoteOn": lambda indexGlobal, note, velocity, channel=-1: W("channels", "midiNoteOn", (indexGlobal, note, velocity), lambda: chan(indexGlobal)),
            },
            "patterns": {
                "patternCount": lambda: R("patterns", "patternCount", (), lambda: sum(1 for p in S.patterns.values() if p.get("notes"))),
                "patternNumber": lambda: R("patterns", "patternNumber", (), lambda: S.pattern_current),
                "getPatternName": lambda index: R("patterns", "getPatternName", (index,), lambda: S.patterns[index]["name"]),
                "setPatternName": lambda index, name: W("patterns", "setPatternName", (index, name), lambda: set_(S.patterns[index], "name", name)),
                "getPatternLength": lambda index: R("patterns", "getPatternLength", (index,), lambda: S.patterns[index]["length"]),
                "jumpToPattern": lambda index: W("patterns", "jumpToPattern", (index,), lambda: (S.patterns[index], set_(S.__dict__, "pattern_current", index))),
                "selectPattern": lambda index, value=-1, preview=False: W("patterns", "selectPattern", (index, value), lambda: (S.patterns[index], S.pattern_selected.add(index) if value != 0 else S.pattern_selected.discard(index))),
                "findFirstNextEmptyPat": lambda flags, x=-1, y=-1: W("patterns", "findFirstNextEmptyPat", (flags,), lambda: None),
                "isPatternDefault": lambda index: R("patterns", "isPatternDefault", (index,), lambda: (pat(index), not pat(index).get("notes"))[1]),
                "setPatternLength": lambda index, length: W("patterns", "setPatternLength", (index, length), lambda: pat_length(index, length)),
                "incrementPatternLength": lambda index, delta: W("patterns", "incrementPatternLength", (index, delta), lambda: pat_length(index, pat(index)["length"] + delta)),
                "clearPattern": lambda index: W("patterns", "clearPattern", (index,), lambda: pat_clear(index)),
                "isPatternSelected": lambda index: R("patterns", "isPatternSelected", (index,), lambda: (S.patterns[index], index in S.pattern_selected)[1]),
            },
            "plugins": {
                "isValid": lambda index, slotIndex=-1, useGlobalIndex=False: R("plugins", "isValid", (index, slotIndex), lambda: (index, slotIndex) in S.plugins),
                "getPluginName": lambda index, slotIndex=-1, userName=False, useGlobalIndex=False: R("plugins", "getPluginName", (index, slotIndex), lambda: plug(index, slotIndex)["name"]),
                "getParamCount": lambda index, slotIndex=-1, useGlobalIndex=False: R("plugins", "getParamCount", (index, slotIndex), lambda: len(plug(index, slotIndex)["params"])),
                "getParamName": lambda paramIndex, index, slotIndex=-1, useGlobalIndex=False: R("plugins", "getParamName", (paramIndex, index, slotIndex), lambda: param(index, slotIndex, paramIndex)[0]),
                "getParamValue": lambda paramIndex, index, slotIndex=-1, useGlobalIndex=False: R("plugins", "getParamValue", (paramIndex, index, slotIndex), lambda: param(index, slotIndex, paramIndex)[1]),
                "setParamValue": lambda value, paramIndex, index, slotIndex=-1, pickupMode=0, useGlobalIndex=False: W("plugins", "setParamValue", (value, paramIndex, index, slotIndex), lambda: param(index, slotIndex, paramIndex).__setitem__(1, float(value))),
                "getParamValueString": lambda paramIndex, index, slotIndex=-1, useGlobalIndex=False: R("plugins", "getParamValueString", (paramIndex, index, slotIndex), lambda: "%.3f" % param(index, slotIndex, paramIndex)[1]),
                "getColor": lambda index, slotIndex=-1, flag=0, useGlobalIndex=False: R("plugins", "getColor", (index, slotIndex), lambda: plug(index, slotIndex)["color"]),
            },
            "playlist": {
                "trackCount": lambda: R("playlist", "trackCount", (), lambda: len(pl)),
                "getTrackName": lambda index: R("playlist", "getTrackName", (index,), lambda: S._idx(pl, index, 1)["name"]),
                "setTrackName": lambda index, name: W("playlist", "setTrackName", (index, name), lambda: set_(S._idx(pl, index, 1), "name", name)),
                "isTrackMuted": lambda index: R("playlist", "isTrackMuted", (index,), lambda: S._idx(pl, index, 1)["mute"]),
                "muteTrack": lambda index, value=-1: W("playlist", "muteTrack", (index, value), lambda: mute_play(index, value)),
                "isTrackSolo": lambda index: R("playlist", "isTrackSolo", (index,), lambda: S._idx(pl, index, 1)["solo"]),
                "soloTrack": lambda index, value=-1, inGroup=False: W("playlist", "soloTrack", (index, value), lambda: set_(S._idx(pl, index, 1), "solo", tog(S._idx(pl, index, 1)["solo"], value))),
                "getTrackColor": lambda index: R("playlist", "getTrackColor", (index,), lambda: S._idx(pl, index, 1)["color"]),
                "setTrackColor": lambda index, color: W("playlist", "setTrackColor", (index, color), lambda: set_(S._idx(pl, index, 1), "color", color)),
            },
            "arrangement": {
                "addAutoTimeMarker": lambda time, name: W("arrangement", "addAutoTimeMarker", (time, name), lambda: marker_add(time, name)),
                "jumpToMarker": lambda delta, select: W("arrangement", "jumpToMarker", (delta, select), lambda: None),
                "currentTime": lambda snap: R("arrangement", "currentTime", (snap,), lambda: int(T["pos"])),
                "getMarkerName": lambda index: R("arrangement", "getMarkerName", (index,), lambda: S.markers[index][1]),
            },
            "general": {
                "getVersion": lambda: R("general", "getVersion", (), lambda: S.api_level),
                "undo": undo,
                "saveUndo": lambda undoName, flags, update=True: W("general", "saveUndo", (undoName, flags), lambda: S.undos.append(undoName)),
                "getChangedFlag": lambda: R("general", "getChangedFlag", (), lambda: S.changed),
            },
            "ui": {
                "getVersion": lambda mode=4: R("ui", "getVersion", (mode,), lambda: "2026.1.7" if mode == 4 else 26),
                "showWindow": lambda index: W("ui", "showWindow", (index,), lambda: S.windows.__setitem__(index, True)),
                "hideWindow": lambda index: W("ui", "hideWindow", (index,), lambda: S.windows.__setitem__(index, False)),
                "getProgTitle": lambda: R("ui", "getProgTitle", (), lambda: S.title),
            },
            "device": {
                "getName": lambda: R("device", "getName", (), lambda: "Coproducer"),
                "isAssigned": lambda: R("device", "isAssigned", (), lambda: True),
                "midiOutSysex": lambda message: S.outbox.append(bytes(message)),
            },
            "midi": {},
        }

    DEFAULTS = {"int": 0, "float": 0.0, "bool": False, "str": "", "None": None}

    def _generic(self, mname: str, fname: str, spec: dict) -> Callable:
        """A stand-in for an inventory function the fake does not model: reads log the call and return the declared type's zero value; writes
        (functions that return None) log, count as a change and keep the last arguments in self.generic for the tests to read."""
        ret = spec.get("returns", "None")
        names = [q["name"] for q in spec.get("params", [])]

        def f(*args, **kw):
            call_args = tuple(args) + tuple(kw.get(n) for n in names[len(args):] if n in kw)
            if ret == "None":
                self._write(mname, fname, call_args, lambda: self.generic.__setitem__(mname + "." + fname, call_args))
                return None
            return self._read(mname, fname, call_args, lambda: self.generic.get(mname + "." + fname + "#value", self.DEFAULTS.get(ret)))
        def lit(text):
            try:
                return ast.literal_eval(text)
            except (ValueError, SyntaxError):
                return 0  # midi.MaxInt and other constants
        params = [inspect.Parameter(q["name"], inspect.Parameter.POSITIONAL_OR_KEYWORD,
                                    **({} if q.get("default") is None else {"default": lit(q["default"])})) for q in spec.get("params", [])]
        f.__signature__ = inspect.Signature(params)  # the stubs' names and order, as the real functions have them
        f.__name__ = fname
        return f

    def _build(self) -> dict[str, types.ModuleType]:
        mods: dict[str, types.ModuleType] = {}
        self.generic: dict[str, Any] = {}
        explicit = self._functions()
        for mname, funcs in explicit.items():
            m = types.ModuleType(mname)
            for fname, f in funcs.items():
                if self._since(mname, fname) <= self.api_level:
                    setattr(m, fname, f)
            mods[mname] = m
        for key, spec in self._inv.items():  # everything else in the inventory, so every generated op has a function to call
            mname, fname = key.split(".", 1)
            if mname in mods and not hasattr(mods[mname], fname) and int(spec.get("since", 1)) <= self.api_level:
                setattr(mods[mname], fname, self._generic(mname, fname, spec))
        mods["midi"].MIDI_BEGINSYSEX = 0xF0  # type: ignore[attr-defined]
        mods["midi"].MIDI_ENDSYSEX = 0xF7  # type: ignore[attr-defined]
        return mods

    # ------------------------------------------------------------------ install
    def install(self) -> "FakeFL":
        self._saved = {k: sys.modules.get(k) for k in self.modules}
        sys.modules.update(self.modules)
        return self

    def uninstall(self) -> None:
        for k, old in getattr(self, "_saved", {}).items():
            if old is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = old


class FakeEvent:
    """Stand-in for FlMidiMsg as passed to OnSysEx."""

    def __init__(self, sysex: bytes) -> None:
        self.sysex = sysex
        self.handled = False
