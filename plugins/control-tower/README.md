# control-tower

Run a Claude session as a **control tower**: a manager of worker agents in
[Herdr](https://herdr.dev). You hand it a task; it turns the task into a
precise spec, starts worker agents with small contexts, watches them, reads
their reports, and coordinates follow-ups (review, CI fixes, PR comments).

## Skills

| Skill | Use |
| --- | --- |
| `/control-tower:dispatch [task]` | Hand a task to the tower. |

## Flow

1. **Intake**: the tower works out the target repo and asks whether you want
   a grilling interview first.
2. **Spec**: written from the grilling or straight from your description.
   No worker starts until you approve its spec.
3. **Launch**: one Herdr worktree per coding task (a tab for read-only work),
   a worker agent (`claude` by default) named `<role>-<slug>`, and a fixed
   set of worker rules (draft PRs at most, never merge or release).
4. **Watch**: background waits; the tower reads each worker's `report.md`.
5. **Follow-ups**: review, CI and PR-comment workers, each with its own spec.
6. **Escalation**: a Herdr notification only for approval prompts, your
   decisions, expired logins, and merge approvals.
7. **Cleanup**: worktrees and workspaces go; the task folder stays.

Task records live in `~/workspace/control-tower/tasks/<date>-<slug>/`
(`spec.md`, `report.md`, `log.md`, `followups/`).

## Install

From GitHub (needs access to the private repo):

```text
/plugin install control-tower --marketplace nadirollo/skills
```

From a local checkout (e.g. on ai-hub, where the repo is synced to
`~/workspace/skills`):

```bash
claude plugin marketplace add ~/workspace/skills
claude plugin install control-tower@nadirollo-skills --scope user
```

## Requirements

- Run inside a Herdr pane on the machine where workers should run.
- `herdr` 0.9.5 or newer, `gh`, and a supported agent CLI (`claude` by
  default).
- Linux (`/proc` is used for the capacity check).

## Credits

`references/grilling.md` is Matt Pocock's
[`grilling`](https://github.com/mattpocock/skills) skill, MIT licensed; see
`skills/dispatch/references/LICENSE-grilling`.
