"""Serum 2's saved state inside an FL Studio project, read and rebuilt, so a generated preset can be put on a channel without the GUI.

Found by reading sandbox\\serum\\serum_sounds.flp (FL 26.1.7, Serum 2.1.5) on 2026-10-26; nothing here is published by Xfer or Image-Line:

- A Serum 2 channel's plugin event (213, Fruity Wrapper) is a u32 kind, then chunks of (u32 id, u64 size, data). Chunk 53 holds the
  plugin state; 54 the name ("Serum2"), 55 the .vst3 path, 56 the vendor.
- Chunk 53 is a u32 (1), then records of (u32 id, u64 size, data): 1 (64 bytes of FL wrapper data), 3 (the VST3 processor state),
  2 (the VST3 controller state), 4 (FL's list of exposed parameters). Records 1 and 4 are the same on every Serum 2 channel seen.
- The processor and controller states are each one Xfer container, the same layout as a .SerumPreset file: b"XferJson\\0", a u64 JSON
  length, the JSON (sorted keys, compact), a u32 uncompressed length, a u32 format mark (2), then a zstd frame of CBOR. In the state,
  the JSON "hash" is the MD5 of the zstd frame.
- Serum splits a preset between the two: the engine (oscillators, envelopes, filters, LFOs, mod slots, FX) in the processor, the editor
  side (the browser, GUI, the preset's name, author, description and path) in the controller; both carry the arp and clip banks, FX
  racks, LFO shapes, macro 0 and the voice panel. The split used here is the one Serum itself wrote for "CP - Deep Sub".

Whether FL and Serum accept a rebuilt state is proved by a render, not by this file: see docs/SERUM_MCP.md for the checks (an offline
render through pedalboard first, then one load in FL with the person present).
"""
from __future__ import annotations

import hashlib
import json
import struct

PLUGIN_STATE_CHUNK = 53
REC_PROCESSOR, REC_CONTROLLER = 3, 2
MAGIC = b"XferJson\x00"
# Keys the controller state carries besides the preset's own (Serum wrote them for "CP - Deep Sub").
CONTROLLER_EXTRA = {"presetComment": "", "presetHasBeenEdited": False}
META_KEYS = ("presetAuthor", "presetDescription", "presetName")


class SerumStateError(ValueError):
    pass


def _chunks(b: bytes, p: int, head: str) -> tuple[int, list[tuple[int, bytes]]]:
    first = struct.unpack_from("<I", b, p)[0]
    p += 4
    out = []
    while p < len(b):
        if p + 12 > len(b):
            raise SerumStateError("truncated %s chunk header at %d" % (head, p))
        cid, size = struct.unpack_from("<IQ", b, p)
        p += 12
        if p + size > len(b):
            raise SerumStateError("%s chunk %d runs past the end" % (head, cid))
        out.append((cid, b[p:p + size]))
        p += size
    return first, out


def _join(first: int, chunks: list[tuple[int, bytes]]) -> bytes:
    return struct.pack("<I", first) + b"".join(struct.pack("<IQ", cid, len(d)) + d for cid, d in chunks)


def wrapper_chunks(blob: bytes) -> tuple[int, list[tuple[int, bytes]]]:
    """FL's plugin wrapper data (event 213) as (kind, [(chunk id, data)])."""
    return _chunks(bytes(blob), 0, "wrapper")


def is_serum2(blob: bytes) -> bool:
    try:
        _, ch = wrapper_chunks(blob)
    except (SerumStateError, struct.error):
        return False
    return any(cid == 54 and d.rstrip(b"\x00") == b"Serum2" for cid, d in ch)


def read_container(b: bytes) -> tuple[dict, dict]:
    """(metadata, engine data) of one Xfer container (a .SerumPreset file or a state record)."""
    import cbor2
    import zstandard
    if not b.startswith(MAGIC):
        raise SerumStateError("not an Xfer container")
    p = len(MAGIC)
    n = struct.unpack_from("<Q", b, p)[0] & 0xFFFFFFFF          # a .SerumPreset writes (u32 length, u32 0); the state a u64 length
    p += 8
    meta = json.loads(b[p:p + n])
    p += n
    ulen, _mark = struct.unpack_from("<II", b, p)
    p += 8
    raw = zstandard.ZstdDecompressor().decompressobj().decompress(b[p:])
    if len(raw) != ulen:
        raise SerumStateError("payload is %d bytes, header says %d" % (len(raw), ulen))
    return meta, cbor2.loads(raw)


def write_container(meta: dict, data: dict, level: int = 19) -> bytes:
    """An Xfer container as Serum writes it in a state: sorted compact JSON whose hash is the MD5 of the zstd frame."""
    import cbor2
    import zstandard
    raw = cbor2.dumps(data)
    z = zstandard.ZstdCompressor(level=level).compress(raw)
    js = json.dumps({**meta, "hash": hashlib.md5(z).hexdigest()}, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return MAGIC + struct.pack("<Q", len(js)) + js + struct.pack("<II", len(raw), 2) + z


def read_state(blob: bytes) -> dict:
    """The parts of a Serum 2 channel's state: {'kind', 'chunks', 'records', 'processor': (meta, data), 'controller': (meta, data)}."""
    kind, ch = wrapper_chunks(blob)
    st = next((d for cid, d in ch if cid == PLUGIN_STATE_CHUNK), None)
    if st is None:
        raise SerumStateError("no plugin state chunk (53)")
    first, recs = _chunks(st, 0, "state")
    got = dict(recs)
    if REC_PROCESSOR not in got or REC_CONTROLLER not in got:
        raise SerumStateError("the state has no processor or controller record (records: %s)" % [r for r, _ in recs])
    return {"kind": kind, "chunks": ch, "first": first, "records": recs,
            "processor": read_container(got[REC_PROCESSOR]), "controller": read_container(got[REC_CONTROLLER])}


def preset_name(blob: bytes) -> str | None:
    try:
        return read_state(blob)["controller"][0].get("presetName")
    except (SerumStateError, ValueError, struct.error):
        return None


UI_FIELDS = ("name", "displayName", "defaultPlainValues")


def _is_ui(key: str) -> bool:
    return key.startswith("kUIParam") or key in UI_FIELDS


def engine_part(v):
    """The part of a preset value the processor keeps: everything but the editor's fields, with 'default' parameter sets written as {}."""
    if isinstance(v, dict):
        return {k: ({} if k == "plainParams" and x == "default" else engine_part(x)) for k, x in v.items() if not _is_ui(k)}
    if isinstance(v, list):
        return [engine_part(x) for x in v]
    return v


def ui_part(v):
    """The editor's fields of a preset value (macro names, display names, kUIParam switches), with the nesting kept."""
    if isinstance(v, dict):
        out = {}
        for k, x in v.items():
            if _is_ui(k):
                out[k] = x
            elif isinstance(x, (dict, list)):
                sub = ui_part(x)
                if sub:
                    out[k] = sub
        return out
    if isinstance(v, list):
        parts = [ui_part(x) for x in v]
        return parts if any(parts) else []
    return {}


def split_preset(preset: dict, template: dict, preset_path: str = "") -> tuple[tuple[dict, dict], tuple[dict, dict]]:
    """((processor meta, data), (controller meta, data)) for a preset (read_container of a .SerumPreset), split the way Serum splits
    its own state: the engine part of each key to the processor, the editor part (kUIParam switches, names) to the controller. A working
    channel's state (read_state) gives which top-level keys each side has and the values for keys the preset leaves out (mod slots past
    the last one it uses, the locks). The preset's own format version is kept; Serum reads that version from preset files."""
    pmeta, pdata = preset
    tproc_meta, tproc = template["processor"]
    tctl_meta, tctl = template["controller"]
    proc = {k: ({"plainParams": {}} if k.startswith("ModSlot") else v) for k, v in tproc.items()}
    proc.update({k: engine_part(v) for k, v in pdata.items() if k in tproc})
    proc["component"] = "processor"
    ctl = {k: v for k, v in tctl.items() if k not in pdata}
    for k, v in pdata.items():
        if k in tproc and isinstance(v, (dict, list)):          # an engine key: the controller keeps only its editor half, when it has one
            ui = ui_part(v)
            if ui:
                ctl[k] = ui
            elif k in tctl:
                ctl[k] = None if tctl[k] is None else type(tctl[k])()
        elif k in tctl and k not in tproc:                      # an editor-only key (browser, GUI, oscillator views): the whole value
            ctl[k] = v
        elif k in tctl:                                         # product, vendor, url, versions: as the controller itself wrote them
            ctl[k] = tctl[k]
    ctl.update(CONTROLLER_EXTRA, component="controller", selectedPresetPath=preset_path)
    for k in META_KEYS:
        ctl[k] = pmeta.get(k, pdata.get(k, ""))
    proc_meta = {**{k: tproc_meta[k] for k in tproc_meta if k != "hash"}, "component": "processor"}
    ctl_meta = {**{k: tctl_meta[k] for k in tctl_meta if k != "hash"}, "component": "controller", "presetComment": ""}
    for k in META_KEYS:
        ctl_meta[k] = ctl[k]
    return (proc_meta, proc), (ctl_meta, ctl)


def build_blob(template_blob: bytes, processor: tuple[dict, dict], controller: tuple[dict, dict]) -> bytes:
    """A channel's plugin event data with new processor and controller states; every other chunk and record kept byte for byte."""
    t = read_state(template_blob)
    new_rec = {REC_PROCESSOR: write_container(*processor), REC_CONTROLLER: write_container(*controller)}
    recs = [(rid, new_rec.get(rid, d)) for rid, d in t["records"]]
    st = _join(t["first"], recs)
    return _join(t["kind"], [(cid, st if cid == PLUGIN_STATE_CHUNK else d) for cid, d in t["chunks"]])


def inject_preset(template_blob: bytes, preset_bytes: bytes, preset_path: str = "") -> bytes:
    """A Serum 2 channel's plugin data that opens with the given .SerumPreset loaded (pending the load checks in docs/SERUM_MCP.md)."""
    if not is_serum2(template_blob):
        raise SerumStateError("the template channel is not Serum 2")
    proc, ctl = split_preset(read_container(preset_bytes), read_state(template_blob), preset_path)
    return build_blob(template_blob, proc, ctl)


def components(blob: bytes) -> tuple[bytes, bytes]:
    """(processor state, controller state) bytes, the VST3 IComponent and IEditController streams, for another host (pedalboard)."""
    got = dict(read_state(blob)["records"])
    return got[REC_PROCESSOR], got[REC_CONTROLLER]


def from_components(template_blob: bytes, processor_state: bytes, controller_state: bytes) -> bytes:
    """A channel's plugin data holding the given VST3 states as raw bytes (for example the ones Serum itself wrote back after loading
    a preset in another host): every other chunk and record of the template kept byte for byte."""
    read_container(processor_state), read_container(controller_state)       # both must parse before they go into a project
    t = read_state(template_blob)
    new_rec = {REC_PROCESSOR: bytes(processor_state), REC_CONTROLLER: bytes(controller_state)}
    st = _join(t["first"], [(rid, new_rec.get(rid, d)) for rid, d in t["records"]])
    return _join(t["kind"], [(cid, st if cid == PLUGIN_STATE_CHUNK else d) for cid, d in t["chunks"]])


# ---------------------------------------------------------------------------------------------------- another VST3 host (JUCE, pedalboard)
# pedalboard (JUCE) keeps a VST3 plugin's state as JUCE binary XML: the magic "VC2!" (0x21324356), a u32 length, then
# <VST3PluginState><IComponent>..</IComponent><IEditController>..</IEditController></VST3PluginState> with each state in JUCE's own
# base64 (MemoryBlock::toBase64Encoding: "size." then 6 bits per character, least significant bits first, from the table below), then a
# null byte. Read back from Serum 2 under pedalboard 0.9.26 on 2026-10-26, and rebuilt byte for byte.
JUCE_MAGIC = 0x21324356
JUCE_B64 = ".ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+"


def juce_b64_encode(b: bytes) -> str:
    n = (len(b) * 8 + 5) // 6
    bits = int.from_bytes(bytes(b), "little")
    return "%d.%s" % (len(b), "".join(JUCE_B64[(bits >> (6 * i)) & 63] for i in range(n)))


def juce_b64_decode(s: str) -> bytes:
    size, _, body = s.partition(".")
    bits = 0
    for i, ch in enumerate(body):
        bits |= JUCE_B64.index(ch) << (6 * i)
    return (bits & ((1 << (8 * int(size))) - 1)).to_bytes(int(size), "little")


def juce_state(processor_state: bytes, controller_state: bytes) -> bytes:
    xml = ('<?xml version="1.0" encoding="UTF-8"?> <VST3PluginState><IComponent>%s</IComponent><IEditController>%s</IEditController>'
           '</VST3PluginState>' % (juce_b64_encode(processor_state), juce_b64_encode(controller_state)))
    body = xml.encode("utf-8") + b"\x00"
    return struct.pack("<II", JUCE_MAGIC, len(body) - 1) + body


def parse_juce_state(raw: bytes) -> tuple[bytes, bytes]:
    """(processor state, controller state) from a JUCE VST3 state (pedalboard's raw_state)."""
    import re
    raw = bytes(raw)
    if struct.unpack_from("<I", raw, 0)[0] != JUCE_MAGIC:
        raise SerumStateError("not a JUCE plugin state")
    m = re.search(rb"<IComponent>([^<]*)</IComponent>", raw)
    c = re.search(rb"<IEditController>([^<]*)</IEditController>", raw)
    if not m or not c:
        raise SerumStateError("the JUCE state has no IComponent or IEditController")
    return juce_b64_decode(m.group(1).decode("ascii")), juce_b64_decode(c.group(1).decode("ascii"))
