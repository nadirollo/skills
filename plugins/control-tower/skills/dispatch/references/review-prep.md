# Review prep

Adapted from Timo Freiberg's
[`review-prep`](https://github.com/TimoFreiberg/dotfiles/blob/main/agents/skills/review-prep/SKILL.md)
skill. It prepares the user to sign off on a change they did not write line
by line: what they are approving, and what the codebase will contain
afterwards. Nothing here posts comments, edits code, or gives a merge
verdict.

Run it when the approval had **review prep** checked and the workers are
done with a code change (a branch or a draft PR). That approval covers this
one read-only reviewer, on the reviewer harness, model and effort it named;
it needs no separate spec approval.

- Name: `review-<slug>`, label `ct.role=review`.
- Working directory: the task's worktree, or the repo for read-only work.
- First prompt: `references/worker-prompt.md`, with the spec below written
  to a temporary file outside the task folder (`mktemp`), and its path as
  `<spec-path>`. Delete that file when the reviewer has reported.
- It reports with `hc send` like any worker, in the format below. Fold the
  report into `summary.md`'s Review section in the same turn.

Fill in:

- `<scope>`: each worker's branch and base (`<base>...<branch>`), and the
  draft PR URLs if there are any.
- `<intent>`: the path of the approved `spec.md`, and the Results section of
  `summary.md`.

~~~markdown
# Review prep for <task title>

## Goal

Prepare the user to sign off on the change in <scope> without reading every
line: explain what it does, and find what is wrong or unneeded in it.

## Context

- Change: <scope>. Read the diff with `git diff <base>...<branch>`, or
  `gh pr diff <pr>`.
- Stated intent: <intent>.

## Decisions made

- Read-only. Do not edit, commit, push, or post comments anywhere.
- Report only findings you can point at in the code. No style nits.
- Cite `file:line` for every claim about the code, and label inference as
  such.

## Acceptance criteria

- [ ] The brief explains the change to a reader who knows the product but
  not this change.
- [ ] Every finding has `file:line`, a severity (critical, high, medium or
  low), a kind (correctness or leanness), why it matters, and a draft review
  comment the user could post.

## Report format

Send it with `hc send` as your final action, at most 80 lines:

REVIEW <task-id>
Outcome: done | failed
In one sentence: <what the change does>
Brief:
- What it does: <and where it conflicts with the stated intent>
- What the codebase now contains: <new structure, assumptions, upkeep>
- Sharp edges: <surprises, new failure modes, silent behavior changes>
- Beyond the stated intent: <anything the spec did not ask for>
- Hunks worth reading: <file:lines, why; most important first>
Findings (most severe first; "none" if none):
F1 · <severity> · <correctness|leanness> · <file:line> · <one-line title>
  Why: <what breaks, and when; or what is not needed>
  Draft comment: <what the user could post>

Correctness: does the change do what the spec claims, is it wired up and
reachable, would the tests fail if the behavior broke? Leanness: machinery,
configuration, defensive code, abstractions and tests the change does not
need for its stated intent. Skip brief lines with nothing to say.

## Out of scope

- Fixing anything. Judging whether to merge.
~~~

## Putting it on the summary

You only assemble: copy the reviewer's content, do not review the diff
yourself. Where a finding contradicts the brief, say so on both. Order
findings by severity, keeping each one's id, `file:line` and draft comment.
Each critical or high finding also goes into Open questions.
