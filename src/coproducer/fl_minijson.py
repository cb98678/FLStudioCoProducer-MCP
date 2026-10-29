"""Tiny JSON codec used inside FL Studio only if the embedded Python has no `json` module.

Inlined into the generated dispatcher. Python 3.9 compatible, standard library only.
Supports dict, list, str, int, float, bool, None. Tested against the real json module.
"""
from __future__ import annotations


def _mj_str(s):
    out = ['"']
    for ch in s:
        o = ord(ch)
        if ch == '"':
            out.append('\\"')
        elif ch == "\\":
            out.append("\\\\")
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif o < 0x20 or o > 0x7E:
            if o > 0xFFFF:
                o -= 0x10000
                out.append("\\u%04x\\u%04x" % (0xD800 + (o >> 10), 0xDC00 + (o & 0x3FF)))
            else:
                out.append("\\u%04x" % o)
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def _mj_dumps(obj, **kw):
    if obj is None:
        return "null"
    if obj is True:
        return "true"
    if obj is False:
        return "false"
    if isinstance(obj, int):
        return str(obj)
    if isinstance(obj, float):
        if obj != obj or obj in (float("inf"), float("-inf")):
            return "null"
        return repr(obj)
    if isinstance(obj, str):
        return _mj_str(obj)
    if isinstance(obj, (list, tuple)):
        return "[" + ",".join(_mj_dumps(x) for x in obj) + "]"
    if isinstance(obj, dict):
        return "{" + ",".join(_mj_str(str(k)) + ":" + _mj_dumps(v) for k, v in obj.items()) + "}"
    raise TypeError("not JSON serializable: " + type(obj).__name__)


def _mj_loads(text):
    pos = [0]
    n = len(text)

    def ws():
        while pos[0] < n and text[pos[0]] in " \t\r\n":
            pos[0] += 1

    def lit(word, value):
        if text.startswith(word, pos[0]):
            pos[0] += len(word)
            return value
        raise ValueError("bad literal at %d" % pos[0])

    def string():
        pos[0] += 1
        out = []
        while pos[0] < n:
            ch = text[pos[0]]
            pos[0] += 1
            if ch == '"':
                return "".join(out)
            if ch != "\\":
                out.append(ch)
                continue
            esc = text[pos[0]]
            pos[0] += 1
            if esc == "u":
                code = int(text[pos[0]:pos[0] + 4], 16)
                pos[0] += 4
                if 0xD800 <= code < 0xDC00 and text.startswith("\\u", pos[0]):
                    low = int(text[pos[0] + 2:pos[0] + 6], 16)
                    pos[0] += 6
                    code = 0x10000 + ((code - 0xD800) << 10) + (low - 0xDC00)
                out.append(chr(code))
            else:
                out.append({"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f", "/": "/", "\\": "\\", '"': '"'}[esc])
        raise ValueError("unterminated string")

    def number():
        start = pos[0]
        while pos[0] < n and text[pos[0]] in "+-0123456789.eE":
            pos[0] += 1
        raw = text[start:pos[0]]
        return float(raw) if any(c in raw for c in ".eE") else int(raw)

    def value():
        ws()
        if pos[0] >= n:
            raise ValueError("unexpected end")
        ch = text[pos[0]]
        if ch == "{":
            pos[0] += 1
            obj = {}
            ws()
            if text[pos[0]] == "}":
                pos[0] += 1
                return obj
            while True:
                ws()
                key = string()
                ws()
                if text[pos[0]] != ":":
                    raise ValueError("expected colon")
                pos[0] += 1
                obj[key] = value()
                ws()
                sep = text[pos[0]]
                pos[0] += 1
                if sep == "}":
                    return obj
                if sep != ",":
                    raise ValueError("expected comma")
        if ch == "[":
            pos[0] += 1
            arr = []
            ws()
            if text[pos[0]] == "]":
                pos[0] += 1
                return arr
            while True:
                arr.append(value())
                ws()
                sep = text[pos[0]]
                pos[0] += 1
                if sep == "]":
                    return arr
                if sep != ",":
                    raise ValueError("expected comma")
        if ch == '"':
            return string()
        if ch == "t":
            return lit("true", True)
        if ch == "f":
            return lit("false", False)
        if ch == "n":
            return lit("null", None)
        return number()

    result = value()
    ws()
    if pos[0] != n:
        raise ValueError("trailing data")
    return result
