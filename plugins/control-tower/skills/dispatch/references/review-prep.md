# Review prep

Adapted from Timo Freiberg's
[`review-prep`](https://github.com/TimoFreiberg/dotfiles/blob/main/agents/skills/review-prep/SKILL.md)
skill. It prepares the user to sign off on a change they did not write line
by line: what they are approving, and what the codebase will contain
afterwards. Nothing here posts comments, edits code, or gives a merge
verdict.

Run it when a worker whose approval had **review prep** checked reports
`done` with a code change (a branch or a draft PR). That approval covers
these three read-only workers, on the reviewer harness, model and effort it
named; they need no separate spec approval. Launch them together, in
parallel, as follow-up `followups/<NN>-review-prep/`, with the normal
capacity check and labels (`ct.role=review`).

| Worker | Name | Output in the follow-up folder |
| --- | --- | --- |
| Correctness reviewer | `review-c-<slug>` | `findings-correctness.md` |
| Leanness reviewer | `review-l-<slug>` | `findings-leanness.md` |
| Brief writer | `brief-<slug>` | `brief.md` |

Each gets its own `spec-<role>.md` from the matching section below, the
normal worker prompt (`references/worker-prompt.md`) with its output file as
the report path, and as its working directory the task's worktree, or the
repo when the worker had none. Before starting them, write each output file
with only `Outcome: pending`.

Fill in for all three:

- `<scope>`: the branch and base (`<base>...<branch>`), and the draft PR URL
  if there is one.
- `<intent>`: the path of the implementing worker's approved `spec.md` (the
  stated intent), and its `report.md`.

## Correctness reviewer spec

~~~markdown
# Review prep: correctness of <worker-name>'s change

## Goal

Find what is wrong in the change in <scope>, so the user can sign off on it.
Does it do what the spec claims, is it wired up and reachable, and would the
tests fail if the behavior broke?

## Context

- Change: <scope>. Read the diff with `git diff <base>...<branch>`, or
  `gh pr diff <pr>`.
- Stated intent: <intent>.

## Decisions made

- Read-only. Do not edit, commit, push, or post comments anywhere.
- Report only findings you can point at in the code. No style nits.

## Acceptance criteria

- [ ] Every finding has `file:line`, the quoted code, a severity
  (critical, high, medium or low), why it is wrong, and a draft review
  comment the user could post.
- [ ] The output follows the format below, ordered by severity.

## Output format

Outcome: done

## Findings

### C1 · <severity> · <one-line title>

- Where: `<file>:<line>`
- Code:
  ```<lang>
  <quoted lines>
  ```
- Why: <what breaks, and when>
- Draft comment: <what the user could post>

(Write "None." under Findings if there are none.)

## Out of scope

- Leanness (unneeded code), and explaining the change: other reviewers do
  those.

## Report path

<followup-dir>/findings-correctness.md
~~~

## Leanness reviewer spec

The same as the correctness spec, with these changes:

- Title and goal: "Leanness of <worker-name>'s change": flag machinery,
  configuration, defensive code, abstractions and tests the change does not
  need for its stated intent.
- Finding ids `L1`, `L2`, ...; output file `findings-leanness.md`.
- Out of scope: correctness bugs, and explaining the change.

## Brief writer spec

~~~markdown
# Review prep: brief for <worker-name>'s change

## Goal

Explain the change in <scope> to a reader who knows the product but not
this change, so they can sign off on it without reading every line.

## Context

- Change: <scope>. Read the diff with `git diff <base>...<branch>`, or
  `gh pr diff <pr>`.
- Stated intent: <intent>.

## Decisions made

- Read-only. Do not edit, commit, push, or post comments anywhere.
- Skip any section with nothing to say. Cite `file:line` for every claim
  about the code, and label inference as such.

## Acceptance criteria

- [ ] The output has the sections below, each concise.

## Output format

Outcome: done

## In one sentence

<What the change does.>

## What it does

<What the change does, and where it conflicts with the stated intent.>

## What the codebase now contains

<New structure and flow, the assumptions it makes, and what someone will
have to maintain.>

## Sharp edges

<Surprises, new failure modes, behavior that changed silently.>

## Beyond the stated intent

<Anything the change does that the spec did not ask for.>

## Hunks worth reading

1. `<file>:<lines>`: <why, ranked by importance>

## Out of scope

- Finding bugs or unneeded code: other reviewers do that.

## Report path

<followup-dir>/brief.md
~~~

## Putting the page together

When all three report (`Outcome: done`, or a failure you note on the page),
build `report.html` beside the implementing worker's `report.md`, from
`references/report-review.html`. You only assemble: copy their content, do
not review the diff yourself. Then:

- Where a finding contradicts the brief, say so on both: a note in the brief
  section naming the finding id.
- Order findings by severity across both reviewers; keep each one's id,
  `file:line`, quoted code and draft comment.
- End with the questions the user still has to answer before signing off:
  each open question from the report, each critical or high finding, and
  each conflict with the stated intent.
