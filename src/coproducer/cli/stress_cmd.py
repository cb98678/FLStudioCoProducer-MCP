"""Live stress test of the real MIDI bridge into FL Studio. Read-only: it never changes the project.

Every scenario ends with a heartbeat ping. The bridge passes a scenario when it neither hangs nor stays deaf afterwards, whatever junk it was sent.
Run with:  coproducer probe stress   (FL open with the Coproducer script selected; it can be any project, nothing is written).
"""
from __future__ import annotations

import random
import statistics
import threading
import time

PREFIX = [0xF0, 0x7D, 0x43, 0x50]
BAD_INDEXES = [-1, -2 ** 31, 0, 1, 127, 128, 16383, 16384, 2 ** 31, 2 ** 53, 2 ** 63, 2 ** 64, 10 ** 30, 1.5, -0.0, float("nan"), float("inf"),
               None, True, "0", "x", "", "A" * 300, [], [0], {}, {"a": 1}]
READ_OPS = ["op_mixer_get_track_name", "op_mixer_get_track_volume", "op_mixer_is_track_muted", "op_mixer_get_track_pan", "op_channels_get_channel_name",
            "op_playlist_get_track_name", "op_patterns_get_pattern_name", "op_patterns_is_pattern_default", "op_arrangement_get_marker_name",
            "op_plugins_get_plugin_name", "op_plugins_is_valid", "op_mixer_get_eq_gain", "op_mixer_get_route_to_level"]
NO_ARG_OPS = ["op_mixer_track_count", "op_patterns_pattern_count", "op_playlist_track_count", "op_transport_is_playing", "op_general_get_version",
              "op_ui_get_prog_title", "op_mixer_get_current_tempo", "op_channels_channel_count", "op_transport_get_song_length"]


def raw_frame(version, msg_type, req_id, seq, total, payload, checksum_delta=0, terminate=True) -> bytes:
    """A frame built without any validation, so it can be wrong in exactly the way a test needs."""
    body = [version & 0x7F, msg_type & 0x7F, (req_id >> 7) & 0x7F, req_id & 0x7F, (seq >> 7) & 0x7F, seq & 0x7F, (total >> 7) & 0x7F, total & 0x7F]
    body += [b & 0x7F for b in payload]
    return bytes(PREFIX + body + [(sum(body) + checksum_delta) & 0x7F] + ([0xF7] if terminate else []))


def _row(name: str, passed: bool, detail: str, **stats) -> dict:
    return {"scenario": name, "passed": passed, "detail": detail, **stats}


def alive(client, tries: int = 3, timeout_s: float = 3.0) -> bool:
    for _ in range(tries):
        if client.ping(timeout_s=timeout_s).ok:
            return True
    return False


def latency(client, n: int = 300) -> dict:
    times, fails = [], 0
    for _ in range(n):
        t0 = time.perf_counter()
        fails += not client.ping(timeout_s=2.0).ok
        times.append((time.perf_counter() - t0) * 1000)
    times.sort()
    s = {"n": n, "fail": fails, "min_ms": round(times[0], 1), "median_ms": round(statistics.median(times), 1),
         "p95_ms": round(times[int(n * 0.95)], 1), "max_ms": round(times[-1], 1)}
    return _row("ping latency", fails == 0, "%d pings, %d failed, median %.1f ms, p95 %.1f ms, max %.1f ms" % (n, fails, s["median_ms"], s["p95_ms"], s["max_ms"]), **s)


def read_soak(client, n: int = 600) -> dict:
    rng, bad, slow = random.Random(7), [], 0
    for i in range(n):
        op = rng.choice(NO_ARG_OPS)
        t0 = time.perf_counter()
        r = client.request(op, {})
        slow += (time.perf_counter() - t0) > 1.0
        if not r.ok and r.error.code in ("E_TIMEOUT", "E_INTERNAL"):
            bad.append("%s %s" % (op, r.error.code))
    return _row("read soak", not bad, "%d reads, %d timeouts or internal errors, %d slower than 1 s" % (n, len(bad), slow), failures=bad[:10])


def bad_arguments(client) -> dict:
    """Wrong-typed and out-of-range arguments straight to FL (bypassing the host schema): FL must answer, with a value or an error."""
    unanswered, crashes, total = [], [], 0
    for op in READ_OPS:
        for bad in BAD_INDEXES:
            total += 1
            r = client.request(op, {"index": bad, "slotIndex": bad, "band": bad, "destIndex": bad}, timeout_s=3.0)
            if not r.ok and r.error.code == "E_TIMEOUT":
                unanswered.append("%s index=%r" % (op, bad))
                if not alive(client):
                    crashes.append("bridge stopped answering after %s index=%r" % (op, bad))
                    break
        if crashes:
            break
    return _row("bad arguments", not unanswered and not crashes, "%d calls, %d unanswered, %d fatal" % (total, len(unanswered), len(crashes)),
                unanswered=unanswered[:15], fatal=crashes)


def payload_sizes(client) -> dict:
    """The same harmless read with growing junk arguments: tests chunking at max_payload and FL-side reassembly."""
    out, worst = [], None
    for n in (0, 50, 150, 199, 200, 201, 399, 400, 1000, 5000, 20000):
        t0 = time.perf_counter()
        r = client.request("op_mixer_get_track_name", {"index": 0, "junk": "x" * n}, timeout_s=5.0)
        out.append({"junk_chars": n, "ok": r.ok, "code": r.error.code if not r.ok else "", "ms": round((time.perf_counter() - t0) * 1000, 1)})
        if not r.ok and r.error.code == "E_TIMEOUT":
            worst = n
            if not alive(client, tries=5):
                return _row("payload sizes", False, "bridge did not recover after %d junk characters" % n, sizes=out)
    return _row("payload sizes", worst is None, "all sizes answered" if worst is None else "first timeout at %d junk characters" % worst, sizes=out)


def concurrency(client, threads: int = 8, each: int = 40) -> dict:
    """Many threads share one client. Replies must match their own requests. Reports what happens, since the client is a single-wire object."""
    base = [client.request("op_mixer_get_track_name", {"index": i}) for i in range(threads)]
    expected = [("ok", b.value) if b.ok else ("err", b.error.code) for b in base]
    wrong, errors, lock = [], [], threading.Lock()

    def work(i: int) -> None:
        for _ in range(each):
            r = client.request("op_mixer_get_track_name", {"index": i})
            with lock:
                got = ("ok", r.value) if r.ok else ("err", r.error.code)
                if got != expected[i]:
                    (errors if not r.ok else wrong).append("thread %d got %r wanted %r" % (i, got, expected[i]))

    ts = [threading.Thread(target=work, args=(i,)) for i in range(threads)]
    for t in ts:
        t.start()
    for t in ts:
        t.join(120)
    return _row("concurrent callers", not wrong and not errors and alive(client),
                "%d threads x %d calls: %d wrong answers, %d errors" % (threads, each, len(wrong), len(errors)), wrong=wrong[:5], errors=errors[:5])


def id_wraparound(client) -> dict:
    client._rid = 16380
    bad = [r.error.code for r in (client.ping(timeout_s=2.0) for _ in range(12)) if not r.ok]
    return _row("request id wraparound", not bad, "12 pings across the 14-bit id wrap, %d failed" % len(bad), failures=bad)


def stale_replies(client, reg) -> dict:
    """Send requests and never read the replies, then make a normal call: stale replies must not be mistaken for the answer."""
    for _ in range(40):
        frames = client._frames(client._next_id(), 1, "op_mixer_track_count", {})
        if frames.ok:
            reg.call("send_request", frames=frames.value)
    time.sleep(0.5)
    good = client.request("op_playlist_track_count", {})
    count = client.request("op_mixer_track_count", {})
    ok = good.ok and count.ok and good.value != count.value or (good.ok and count.ok)
    return _row("unread replies pile up", ok and alive(client), "after 40 unread replies: playlist_track_count=%s mixer_track_count=%s" % (good.value if good.ok else good.error.code, count.value if count.ok else count.error.code))


def send_raw(transport, data: bytes) -> str:
    """Put bytes on the wire even when the MIDI library refuses them as malformed. Returns '' when sent, else why not."""
    try:
        transport.send(data)
        return ""
    except Exception as first:  # noqa: BLE001 - mido validates messages and rejects exactly the junk this test needs
        raw = getattr(getattr(transport, "out_port", None), "_rt", None)
        if raw is None or not hasattr(raw, "send_message"):
            return "the MIDI library refused it (%s)" % first
        try:
            raw.send_message(list(data))
            return ""
        except Exception as e:  # noqa: BLE001
            return "the MIDI driver refused it (%s)" % e


def garbage(transport, client) -> dict:
    """Raw junk on the wire. After each item the bridge must still answer a ping."""
    rng = random.Random(11)
    items = [
        ("foreign sysex", bytes([0xF0, 0x7E, 0x7F, 0x06, 0x01, 0xF7])),
        ("empty sysex", bytes([0xF0, 0xF7])),
        ("our prefix only", bytes(PREFIX + [0xF7])),
        *[("truncated after %d bytes" % n, bytes((PREFIX + [1, 4, 0, 5, 0, 0, 0, 1])[:n] + [0xF7])) for n in range(4, 12)],
        ("bad checksum", raw_frame(1, 4, 77, 0, 1, [], checksum_delta=1)),
        ("version 99", raw_frame(99, 4, 78, 0, 1, [])),
        ("message type 0", raw_frame(1, 0, 79, 0, 1, [])),
        ("message type 6", raw_frame(1, 6, 80, 0, 1, [])),
        ("message type 127", raw_frame(1, 127, 81, 0, 1, [])),
        ("total 0", raw_frame(1, 1, 82, 0, 0, [])),
        ("seq beyond total", raw_frame(1, 1, 83, 5, 2, [0, 1, 2])),
        ("request id 0", raw_frame(1, 4, 0, 0, 1, [])),
        ("request id 16383", raw_frame(1, 4, 16383, 0, 1, [])),
        ("total 16383", raw_frame(1, 1, 84, 0, 16383, [0, 1, 2])),
        ("5000 byte payload in one frame", raw_frame(1, 1, 85, 0, 1, [rng.randrange(128) for _ in range(5000)])),
        ("random payload as a request", raw_frame(1, 1, 86, 0, 1, [rng.randrange(128) for _ in range(60)])),
        ("incomplete multi-frame (1 of 3)", raw_frame(1, 1, 87, 0, 3, [rng.randrange(128) for _ in range(20)])),
        ("incomplete multi-frame (2 of 3)", raw_frame(1, 1, 87, 1, 3, [rng.randrange(128) for _ in range(20)])),
        ("duplicate frame", raw_frame(1, 4, 88, 0, 1, [])),
        ("duplicate frame", raw_frame(1, 4, 88, 0, 1, [])),
        ("unterminated sysex", raw_frame(1, 4, 89, 0, 1, [], terminate=False)),
        ("F0 inside sysex", bytes(PREFIX + [1, 4, 0, 90, 0xF0, 0, 0, 0, 1, 0, 0xF7])),
        *[("random 7-bit sysex %d" % i, bytes([0xF0] + [rng.randrange(128) for _ in range(rng.randrange(1, 300))] + [0xF7])) for i in range(30)],
        *[("random with our prefix %d" % i, bytes(PREFIX + [rng.randrange(128) for _ in range(rng.randrange(1, 300))] + [0xF7])) for i in range(30)],
    ]
    deaf, unsendable = [], []
    for label, data in items:
        why = send_raw(transport, data)
        if why:
            unsendable.append("%s: %s" % (label, why))
            continue
        time.sleep(0.05)
        if not alive(client, tries=3, timeout_s=2.0):
            deaf.append("%s: bridge deaf afterwards" % label)
            for _ in range(5):                       # try to wake it with a clean sysex end, so one finding does not hide the rest
                send_raw(transport, bytes([0xF7]))
                if alive(client, tries=1):
                    break
    return _row("garbage on the wire", not deaf, "%d junk messages sent, %d could not be sent at all, %d left the bridge deaf" % (len(items) - len(unsendable), len(unsendable), len(deaf)),
                deaf=deaf[:20], unsendable=unsendable[:10])


def hostile_op_names(client) -> dict:
    """Odd operation names and argument shapes: the FL-side dispatcher must refuse them and must never run anything it was not given a name for."""
    names = ["", "ping", "nonexistent_op", "__import__", "__class__", "op_", "mixer.getTrackName", "../etc/passwd", "op_mixer_get_track_name\x00x",
             "OP_MIXER_GET_TRACK_NAME", "op_" + "A" * 3000, "\u202eop_mixer_get_track_name", "exec", "eval", "os.system", "op_general_get_version; rm -rf"]
    shapes = [{}, {"index": 0}, {"index": {"__class__": 1}}, {"args": [0]}, {"": ""}, {"index": 0, "extra": [1, 2, 3]}]
    runs, bad = 0, []
    for n in names:
        for s in shapes:
            runs += 1
            r = client.request(n, s, timeout_s=3.0)
            if r.ok and n not in ("op_mixer_get_track_name", "ping") and not n.upper().startswith("OP_MIXER"):
                bad.append("%r %r was accepted" % (n[:40], s))
            if not r.ok and r.error.code == "E_TIMEOUT" and not alive(client):
                bad.append("bridge dead after %r %r" % (n[:40], s))
                break
    return _row("hostile operation names", not bad, "%d calls, %d problems" % (runs, len(bad)), problems=bad[:15])


def reconnect(open_transport, cfg, client_factory, reg_attach) -> dict:
    """Open and close the MIDI ports repeatedly; each new connection must reach FL."""
    fails = []
    for i in range(12):
        opened = open_transport(cfg["midi"]["out"], cfg["midi"]["in"])
        if not opened.ok:
            fails.append("open %d: %s" % (i, opened.error.message[:100]))
            continue
        c = client_factory(opened.value)
        if not alive(c, tries=3, timeout_s=2.0):
            fails.append("connection %d: no answer" % i)
        opened.value.close()
        time.sleep(0.2)
    return _row("reconnect loop", not fails, "12 open/close cycles, %d failed" % len(fails), failures=fails[:10])


def stall_hunt(client, seconds: float = 150.0) -> dict:
    """Ping steadily and note every answer slower than 300 ms with the second it happened. FL freezes its scripts now and then (autosave, a plugin
    scan, a dialog), so this measures how long and how often. Passes when no ping fails and no single stall is longer than 5 seconds."""
    t0, slow, fails, n = time.time(), [], 0, 0
    while time.time() - t0 < seconds:
        s = time.perf_counter()
        r = client.ping(timeout_s=8.0)
        ms = (time.perf_counter() - s) * 1000
        n += 1
        fails += not r.ok
        if ms > 300 or not r.ok:
            slow.append({"at_s": round(time.time() - t0, 1), "ms": round(ms), "ok": r.ok,
                         "error": "" if r.ok else "%s: %s %s" % (r.error.code, r.error.message[:160], r.error.detail)})
    worst = max([x["ms"] for x in slow], default=0)
    return _row("stall hunt", fails == 0 and worst <= 5000, "%d pings in %.0f s, %d slower than 300 ms, worst %d ms, %d failed" % (n, seconds, len(slow), worst, fails),
                slow=slow[:30], failures=[])


def desktop_weird(call) -> list:
    """Weird window states, one at a time, each undone afterwards: FL minimized, another program in front, focus thrashing, a screenshot while minimized.

    The desktop checks must answer (ready, or a clear refusal) and must never raise or hang. No clicks and no keys are sent to FL."""
    import ctypes
    import subprocess
    import sys
    if sys.platform != "win32":
        return [_row("desktop weirdness", True, "skipped: not Windows")]
    from ..desktop_win import WinDesktop
    d, u, rows = WinDesktop(), ctypes.windll.user32, []

    def answer(label: str, fn) -> dict:
        t0 = time.perf_counter()
        try:
            r = fn()
            took = time.perf_counter() - t0
            return _row(label, took < 20, "%s in %.1f s" % ("ok" if r.ok else "refused %s: %s" % (r.error.code, r.error.message[:90]), took))
        except Exception as e:  # noqa: BLE001 - raising is the finding
            return _row(label, False, "raised %s: %s" % (type(e).__name__, e))

    win = d.find_window()
    if not win:
        return [_row("desktop weirdness", False, "FL's main window was not found; open FL with a project and retry")]
    h = win["handle"]
    try:
        rows.append(answer("baseline ready check", lambda: call("check_desktop_ready")))
        u.ShowWindow(h, 6)                                   # minimize
        time.sleep(0.6)
        rows.append(answer("FL minimized: ready check", lambda: call("check_desktop_ready")))
        u.ShowWindow(h, 6)
        time.sleep(0.4)
        rows.append(answer("FL minimized: screenshot", lambda: call("take_screenshot", out_path="sandbox/screens/stress_min.png")))
        u.ShowWindow(h, 9)
        time.sleep(0.6)
        rows.append(answer("FL restored: ready check", lambda: call("check_desktop_ready")))
        pad = subprocess.Popen(["notepad.exe"])
        time.sleep(2.0)
        try:
            rows.append(answer("another program in front: ready check", lambda: call("check_desktop_ready")))
        finally:
            pad.terminate()
            time.sleep(0.5)
        flips = 0
        for _ in range(15):
            u.ShowWindow(h, 6)
            time.sleep(0.15)
            flips += bool(d.focus(h))
        rows.append(_row("focus thrash", flips >= 12, "%d of 15 minimize and refocus cycles got the focus back" % flips))
        rows.append(answer("after the thrash: ready check", lambda: call("check_desktop_ready")))
    finally:
        u.ShowWindow(h, 9)
        time.sleep(0.4)
        d.focus(h)
    return rows


def run_all(client, reg, transport, only: list | None = None) -> list:
    """Run every scenario (or the named ones) in the order that finds problems cheapest first. Stops early if the bridge cannot be woken."""
    plan = [("latency", lambda: latency(client)), ("reads", lambda: read_soak(client)), ("args", lambda: bad_arguments(client)),
            ("payload", lambda: payload_sizes(client)), ("ops", lambda: hostile_op_names(client)), ("wrap", lambda: id_wraparound(client)),
            ("stale", lambda: stale_replies(client, reg)), ("threads", lambda: concurrency(client)), ("garbage", lambda: garbage(transport, client))]
    if only and "stalls" in only:
        plan.append(("stalls", lambda: stall_hunt(client)))
    rows = []
    for key, fn in plan:
        if only and key not in only:
            continue
        t0 = time.time()
        try:
            row = fn()
        except Exception as e:  # noqa: BLE001 - a scenario that crashes the harness is itself a finding
            row = _row(key, False, "scenario raised %s: %s" % (type(e).__name__, e))
        row["seconds"] = round(time.time() - t0, 1)
        row["alive_after"] = alive(client, tries=5, timeout_s=3.0)
        rows.append(row)
        if not row["alive_after"]:
            rows.append(_row("abort", False, "the bridge stopped answering after '%s'; later scenarios skipped" % key))
            break
    return rows


def render(rows: list) -> str:
    lines = []
    for r in rows:
        lines.append("%s  %-26s %s  (%ss)" % ("PASS" if r["passed"] else "FAIL", r["scenario"], r["detail"], r.get("seconds", "")))
        for k in ("failures", "wrong", "errors", "unanswered", "fatal", "deaf", "problems"):
            for item in r.get(k, [])[:6]:
                lines.append("        %s: %s" % (k, item))
    lines.append("")
    lines.append("%d passed, %d failed" % (sum(r["passed"] for r in rows), sum(not r["passed"] for r in rows)))
    return "\n".join(lines)
