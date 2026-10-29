# Self-check before you answer

- [ ] One public function; file name, folder name and function name are the same.
- [ ] Every parameter and the return value are annotated. Return type is `Result` (L1 ops inside FL return a plain dict).
- [ ] No `raise`, no bare `except`.
- [ ] Imports are only those the card allows.
- [ ] Every `call("...")` uses a literal name and is listed in `deps.calls`.
- [ ] Docstring of 6 lines or fewer that names the error codes.
- [ ] Tests: one per acceptance case, one failure case per error code, golden and failure named in the manifest.
- [ ] A module that changes state sets `verified` in its Result metadata and its golden test asserts it.
- [ ] Nothing from the card's Out of scope field was added.
- [ ] Exactly three fenced blocks, each labeled with its path.
