"""Small pure helpers for the mix loop: level of a part at its own hits, warnings for edits aimed at bypassed slots, A/B headline deltas.

Kept free of FL and of the registry so they test without a machine. tools/mix_iter.py and tools/mix_compare.py are the command lines.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import butter, sosfilt

SLOT_EDIT_MODULES = ("set_plugin_param_by_name", "apply_param_recipe", "op_plugins_set_param_value")


def hit_levels(x: np.ndarray, sr: int, bpm: float, bars: list[int], hits: dict[str, tuple[list[float], float, float]],
               window_s: float = 0.08, shift_steps: float = 0.0) -> dict[str, dict[int, list[float]]]:
    """Band-limited RMS in dB in a short window after each expected hit.

    hits maps a name to (steps in the bar, low Hz, high Hz). Returns {name: {bar: [dB per step]}}. A hit that is not in the render reads very low.
    """
    x = x.mean(1) if x.ndim > 1 else x
    step = 60.0 / bpm / 4
    out: dict[str, dict[int, list[float]]] = {}
    for name, (steps, lo, hi) in hits.items():
        sos = butter(4, [lo, min(hi, sr / 2 - 100)], btype="band", fs=sr, output="sos")
        out[name] = {}
        for bar in bars:
            row = []
            for s in steps:
                i = int(round((bar * 16 + s + shift_steps) * step * sr))
                seg = x[max(0, i - 200) : i + int(window_s * sr)]
                y = sosfilt(sos, seg) if len(seg) > 32 else np.zeros(1)
                row.append(round(float(20 * np.log10(np.sqrt(np.mean(y**2)) + 1e-9)), 1))
            out[name][bar] = row
    return out


def mean_level(levels: dict[int, list[float]]) -> float:
    vals = [v for row in levels.values() for v in row]
    return round(float(np.mean(vals)), 1) if vals else float("nan")


def bypassed_edit_warnings(edits: list[dict], slot_states: dict[int, list[dict]]) -> list[str]:
    """Warn about edits that target an effect slot which is bypassed, since their readback is verified yet inaudible.

    edits are {"module", "args"} dicts, slot_states maps a mixer track to the rows list_effect_slots returns.
    """
    out = []
    for e in edits:
        if e.get("module") not in SLOT_EDIT_MODULES:
            continue
        a = e.get("args", {})
        track, slot = a.get("index"), a.get("slot_index", a.get("slotIndex", -1))
        if track is None or slot is None or slot < 0:
            continue
        row = next((r for r in slot_states.get(track, []) if r["slot"] == slot), None)
        if row is None:
            out.append("track %s slot %s: no plugin found there" % (track, slot))
        elif row.get("active") is False:
            out.append("track %s slot %s (%s) is bypassed: this edit will read back as verified but will not change the sound" % (track, slot, row["plugin"]))
    return out


def headline_delta(a: dict, b: dict) -> dict:
    """b minus a for the numbers in a measure report (lufs, tp, crest, centroid and each band)."""
    out = {k: round(b[k] - a[k], 2) for k in ("lufs", "tp", "crest", "centroid") if k in a and k in b}
    out.update({"band_" + k: round(b["bands"][k] - a["bands"][k], 2) for k in a.get("bands", {}) if k in b.get("bands", {})})
    return out
