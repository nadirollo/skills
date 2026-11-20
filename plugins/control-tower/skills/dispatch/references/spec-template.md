# Spec template

Write one `spec.md` per task. Every worker reads this file and its worker
prompt, and nothing else, so the spec must stand on its own: no "as
discussed", no references to the tower's conversation. Keep it short. If a
section would be empty, write "None." rather than dropping it. How each
worker runs (harness, model, effort) is not part of the spec: the user picks
it at approval.

```markdown
# <Task title>

- Task: <task-id>
- Revision: <N>

## Goal

<One paragraph: the outcome, and why it matters.>

## Context

- Repo: <path>
- Relevant files: <paths, with one line each on why they matter>
- Links: <PR, issue, CI run, docs: only ones a worker must read>

## Decisions made

<Every decision settled with the user, one bullet each, phrased as a rule
workers must follow. From the grilling and the user's review of this spec.
Workers must not reopen these.>

## Work split

<One subsection per worker. Prefer one worker; split only into pieces that
can proceed independently.>

### <worker-name> (<role>)

- Does: <its part of the goal, in one or two lines>
- Working directory: <worktree path, or the repo for read-only work>
- Branch: <branch, or "none (read-only)">

## Acceptance criteria

<Checkable statements. Each one names how to check it (a command, a test, a
file that must exist, a CI check that must pass) and, with several workers,
which worker it belongs to.>

- [ ] ...

## Stop points

<When a worker must stop and report instead of carrying on: a decision the
spec does not settle, a change outside its working directory, a failing
check it cannot fix within scope, anything that would need a forbidden
action.>

## Out of scope

<What workers must not do or change, even if it seems helpful.>

## Standing yes

<Worker prompts the user said the tower may answer for this task, quoted
exactly as the user said them, each with the date and the workers it covers.
"None." until the user gives one.>
```

`Standing yes` is the only section the tower may edit after approval
without a new revision: it records the user's own words, not a change to
the work.
