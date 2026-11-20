# Summary template

`summary.md` is the task's only record besides `spec.md`, and the tower is
its only writer. Create it at launch. Update it in place, in the same turn
something happens: a worker starts, a report arrives, the review is in, the
user decides. Never append a log: each section holds the state now. If the
tower restarts or its context is compacted, this file and `spec.md` are what
it resumes from.

```markdown
# Summary: <Task title>

- Task: <task-id>
- Spec: revision <N>, approved <YYYY-MM-DD HH:MM>
- Status: running | waiting-on-user | ready-for-sign-off | signed-off | abandoned

## In short

<Two or three sentences for the user: what was done, what it means, what is
left. Rewrite it whenever a report changes the picture.>

## Workers

| Worker | Role | Runs as | Working directory · branch | Outcome |
| --- | --- | --- | --- | --- |
| <name> | <role> | <harness · model · effort> | <path · branch> | running / done / blocked / failed |

## Results

### <worker-name>

- Changed: <commits, branch, draft PR, files; "None." for read-only work>
- Evidence: <one line per acceptance criterion: met / not met / no evidence,
  with the decisive line from the report>
- Open questions: <from the report, or "None.">

## Review

<Only when review prep ran: the reviewer's brief, then its findings by
severity, as `references/review-prep.md` gives them. Otherwise "Not run.">

## Open questions

<Everything the user still has to answer: open questions from the reports,
critical or high findings, conflicts with the spec. "None." if nothing.>

## Decision

<The user's sign-off decision, finding dispositions and answers, once given.
"Pending." until then.>
```

The tower writes only what the reports, the reviewer and the user said. It
checks each "met" against the spec's acceptance criteria itself, and marks a
claim without evidence as "no evidence".
