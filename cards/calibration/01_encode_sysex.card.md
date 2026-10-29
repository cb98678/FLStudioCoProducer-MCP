### Card 01. `encode_sysex` (L0, pure)

1. **Goal.** Pack a list of bytes into 7-bit form so it can travel in a SysEx message.
2. **Signature.** `def encode_sysex(data: list[int]) -> Result`
3. **I/O.** Input: list of integers, each 0 to 255. Output `value`: list of integers, each 0 to 127. Errors: `E_ARG` for any element not an integer in 0 to 255.
4. **Sources.** Algorithm defined in file 03, section 4.4, item 1. No FL API used.
5. **Imports and class.** `pure`. Allowed: `typing`, and the Result helpers.
6. **Budget.** 25 lines, nesting 2, 1 parameter.
7. **Acceptance tests.**
   - `[]` returns `[]`.
   - `[0xFF]` returns `[0x01, 0x7F]`.
   - `[0x80, 0x01]` returns `[0x01, 0x00, 0x01]`.
   - Seven bytes of `0xFF` return `[0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F]`.
   - Eight bytes of `0x00` return ten bytes, all zero.
   - For every input in a set of 200 random lists, every output byte is at most 127 (property test).
   - `[256]` returns an `E_ARG` failure. `[-1]` returns `E_ARG`. `["a"]` returns `E_ARG`. `[True]` returns `E_ARG`.
8. **Out of scope.** Framing, checksums, I/O, decoding. Do not mutate the input list.

Derivation note: in each group of up to 7 input bytes, the header byte's bit `i` (value `1 << i`) is the top bit of input byte `i`. The data bytes follow with their top bit cleared. A final partial group of `n` bytes yields `n + 1` bytes.
