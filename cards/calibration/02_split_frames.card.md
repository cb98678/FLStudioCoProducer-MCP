### Card 02. `split_frames` (L0, pure)

1. **Goal.** Split a byte list into consecutive chunks of at most N bytes.
2. **Signature.** `def split_frames(data: list[int], max_len: int) -> Result`
3. **I/O.** `value`: list of lists. Errors: `E_ARG` if `max_len` is less than 1 or `data` is not a list.
4. **Sources.** File 03, section 4.2, item 4. No FL API used.
5. **Imports and class.** `pure`.
6. **Budget.** 15 lines, nesting 2, 2 parameters.
7. **Acceptance tests.**
   - `([0,1,2,3,4], 2)` returns `[[0,1],[2,3],[4]]`.
   - `([], 5)` returns `[]`.
   - `([1,2], 5)` returns `[[1,2]]`.
   - `([1,2,3,4], 4)` returns `[[1,2,3,4]]`.
   - `([1,2,3], 0)` returns `E_ARG`. `("abc", 2)` returns `E_ARG`.
   - Joining the chunks always reproduces the input (property test).
8. **Out of scope.** Headers, sequence numbers, 7-bit checks.
