---
name: module-authoring
description: Use when writing, fixing, or reviewing one module for the FL co-producer from a task card: producing the .py file, module.toml, and tests, and reading lint failures. Use even when the user just says "build this card".
---

# Module authoring

You build exactly one module per card. A module is one function with one job. The card is your whole world: do not browse the repository.

## Steps

1. Read the card fields in order: Goal, Signature, I/O, Sources, Imports and class, Budget, Acceptance tests, Out of scope. If a field is missing, say which one and stop.
2. Write the signature and every failure branch first. Each error code in the card gets a `fail(...)` branch.
3. Write the happy path. Stay inside the budget. If the budget cannot be met, say so and stop; do not squeeze lines together.
4. Write the tests: one test per acceptance case, with the card's numbers. At least one failure test per error code. Name two tests in the manifest: `golden` (the main success) and `failure` (the main error).
5. Fill `module.toml` from the card (see `references/catalog/rules.md` for what the linter checks, and `references/worked-examples.md` for two accepted modules).
6. Check yourself against the rules, then reply with exactly three files: `<name>.py`, `module.toml`, `test_<name>.py`, each in a fenced block labeled with its path. No prose outside the blocks.

## The type you return

- Success: `return ok(value)`. A module that changes state also passes `verified=True` or `verified=False` as metadata: `ok(value, verified=True)`.
- Failure: `return fail("E_CODE", "plain message")`. Never `raise`. Never use a bare `except`.
- Error codes come from the card. Do not invent new ones.

## Composition

- Call another module only with `call("module_name", arg=value)`, with a string literal name, and list every callee in `deps.calls` in the manifest.
- A module may call its own layer or lower layers only. The result of `call(...)` is a Result: check `.ok` before using `.value`.

## Reading a lint report

The report is one line per problem: `LM-005 line 7: import 'os' not allowed for pure/L4`.

1. Fix only the lines the report names.
2. Do not add features, rename things, or reformat other code.
3. Re-check the rule text in `references/catalog/rules.md` if the message is unclear.
4. Reply with the three files again.

## Test against what FL shows, not what is stored

A fake FL must copy real defaults and formats, and a file test must model how FL reads the file. Two fakes were wrong once: the default send level (0.8 in FL, not 1.0) and the colour integer (signed, with an alpha byte). A file organizer once passed every check of its own events while FL showed grey rows and channels in the wrong groups, because the check read the stored values and not the flags and the sort order FL applies. Write the check against the shown value, and when a real file FL saved is available, run the check on it.

## Ask or stop when

- The card contradicts itself or the allowed imports make the job impossible. Say what conflicts. Do not guess.
- A test number in the card cannot be derived. Say which one.

## Never

- Add something the card lists under Out of scope.
- Write an absolute path, an em dash, or a second public function.
- Touch the bridge protocol (L0) or the sandbox check without a human review of the diff.
