### Card NN. `module_name` (L4, reads files)

1. **Goal.** One sentence. One job.
2. **Signature.** `def module_name(path: str) -> Result`
3. **I/O.** Input and output JSON Schema in words or JSON, and every error code the function may return.
4. **Sources.** Exact manual or reference entries for any FL API used, as links to specific pages. For model adapters, the pinned repository commit and README section.
5. **Imports and class.** The side-effect class (pure, reads files, writes files, gui, system, reads fl, writes fl) and the allowed imports. Anything else fails the linter.
6. **Budget.** Lines, nesting depth and parameter count (defaults 40 lines, depth 3, 6 parameters).
7. **Acceptance tests.**
   - Given and expected pairs, with every number derived in the card.
   - At least one failure case per error code.
8. **Out of scope.** The two most likely overreaches, named.
