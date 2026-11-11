# Report template

Before starting a worker, write this skeleton to its `report.md` with
`Outcome: pending`. The worker replaces it with the real report as its last
step. A report still saying `pending` after the worker stops means it never
finished.

```markdown
# Report: <worker-name>

Outcome: pending

<!-- Replace "pending" with exactly one of: done | blocked | failed -->

## What changed

<Commits (hash and subject), branch, draft PR URL, files touched. "None." for
read-only work.>

## Evidence

<Commands run to check each acceptance criterion and their results: test
output, lint, CI status. Quote the decisive lines, not whole logs.>

## Open questions

<Anything needing a decision the spec didn't settle. "None." if nothing.>

## Suggested next step

<One or two lines: e.g. "review the diff", "wait for CI", "ready for merge
approval".>
```
