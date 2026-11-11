# Spec template

Write one `spec.md` per worker. A worker reads only this file and the worker
prompt, so the spec must stand on its own: no "as discussed", no references to
the tower's conversation. Keep it short. If a section would be empty, write
"None." rather than dropping it.

```markdown
# <Task title>

- Task: <task-id>
- Worker: <worker-name>
- Kind: <claude | copilot | ...>

## Goal

<One paragraph: the outcome, and why it matters.>

## Context

- Repo: <path on ai-hub>
- Worktree: <path, or "none (read-only)">
- Branch: <branch, or "none">
- Relevant files: <paths, with one line each on why they matter>
- Links: <PR, issue, CI run, docs: only ones the worker must read>

## Decisions made

<Every decision already settled with the user, one bullet each, phrased as a
rule the worker must follow. From grilling, or from the user's description and
their review of this spec. Workers must not reopen these.>

## Acceptance criteria

<Checkable statements. Each one names how to check it: a command, a test, a
file that must exist, a CI check that must pass.>

- [ ] ...

## Out of scope

<What the worker must not do or change, even if it seems helpful.>

## Report path

<absolute path to report.md>
```
