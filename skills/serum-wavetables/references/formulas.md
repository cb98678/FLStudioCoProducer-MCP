# Formula tables

`build_wavetable` with `formula` evaluates a formula the way Serum's formula parser reads it and writes the frames as a table (serum-mcp
has no formula field). Variables, from the Serum formula documentation as quoted by [makou, 2017](https://www.makou.com/wavetable-making-on-serum/):
x runs from -1 to 1 across one cycle, w is (x+1)/2, y is the table position from 0 to 1 (frame k of n is k/(n-1)). Serum 2 keeps the
formula parser; its own guide ([Serum 2 User Guide](https://xferrecords.com/manual/serum-2), a PDF behind a signed link) could not be
read from here, so the Serum 1 wording is assumed unchanged. Functions: sin, cos, tan, asin, acos, atan, sinh, cosh, tanh, exp, log,
log10, sqrt, abs, sign, floor, ceil, min, max, pow; constants pi and e; ^ is a power. Nothing else is accepted.

Because x is -1 to 1, one sine cycle is `sin(pi*x)`, not `sin(x)`. The report gives `wrap_jump` (the jump from the end of the cycle back
to its start: 0 for a smooth wave, about 2 for a saw) and the first 16 harmonic levels of the first and last frames.

## The two formulas `tools/serum_tables.py` uses

| Name | Formula | What it does (measured by tests/test_wavetables.py) |
| --- | --- | --- |
| PM sub | `sin(pi*x + y*sin(2*pi*x))` | y = 0: a pure sine (every harmonic above the first under -60 dB). Rising y: phase modulation by twice the frequency adds odd harmonics only (3rd, 5th), the warmth that lets a sub read on small speakers. Rendered on G1: a pure sine at Macro 1 = 0 |
| Morph stab | `(1-y)*sin(pi*x) + y*(0.6*sin(3*pi*x) + 0.4*sin(5*pi*x))` | from a sine to the 3rd and 5th harmonics: a dark pluck at the start of the table, hollow and bright at the end. Macro 1 (GRIP) moves it |

## The attachment's formulas, checked

| Attachment | What it actually gives | Use instead |
| --- | --- | --- |
| `sin(x + y * sin(x * 2))`, "a perfectly clean, round sub sine at y=0" | at y = 0, sin(x) over x = -1..1 radians is a third of a sine cycle: a bent ramp with a jump of 1.7 at the wrap, a saw's harmonic series (2nd at 0.46 of the fundamental, 3rd at 0.30). Not a sub | `sin(pi*x + y*sin(2*pi*x))` |
| `cos(3 * acos(x)) * (1 - y) + sin(x * 5) * y`, "Chebyshev 3rd and 5th harmonic distortion" | Chebyshev T3 makes the 3rd harmonic only when its input is a cosine. Here the input is the ramp x, so it is a shaped saw with every harmonic and a jump of 2 at the wrap; `sin(x*5)` is 1.6 cycles, another jump | for the 3rd harmonic of a cosine, `cos(3*acos(cos(pi*x)))` (that is `cos(3*pi*x)`); for a sine morphing to 3rd and 5th, the morph stab above |

A buzz can be the point: a ramp-based formula is a fine saw-like table. Choose it for its sound, knowing what it is.
