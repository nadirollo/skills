# control-tower

Run a Claude session as a **control tower**: a manager of worker agents in
[Herdr](https://herdr.dev) (herdr-app and herdr-core). You hand it a task;
it turns the task into a precise spec, starts worker agents with small
contexts, watches them, reads their reports, and coordinates follow-ups
(review, CI fixes, PR comments).

## Skills

| Skill | Use |
| --- | --- |
| `/control-tower:dispatch [task]` | Hand a task to the tower. |
| `/control-tower:setup [workspace]` | Set up, check or repair the Coder workspace the tower runs on. Run from your laptop. |

## Flow

Each task gets its own herdr-app space. You create the space, start Claude
in it and run `/control-tower:dispatch`; that session is the task's tower.

1. **Intake**: the tower works out the target repo and asks whether you want
   a grilling interview first.
2. **Spec**: written from the grilling or straight from your description.
   No worker starts until you approve its spec.
3. **Launch**: `hc run` starts each worker agent (`claude` by default),
   named `<role>-<slug>`, in a git worktree for coding work or the repo for
   read-only work, with a fixed set of worker rules (draft PRs at most, never
   merge or release). A `herdr.space` label makes each worker a tab in the
   task's space.
4. **Watch**: a background `hc wait --children any`; workers report with
   `hc send`, and the tower reads each worker's `report.md`.
5. **Follow-ups**: review, CI and PR-comment workers, each with its own spec,
   in the same space.
6. **Escalation**: you talk only to the tower. It relays every worker prompt
   or question to you in its own chat (batched, with a recommendation) and
   types your answer into the worker; prompt classes you delegate for the
   task it answers itself and logs. It also asks you for decisions, expired
   logins and merge approvals; herdr-app shows it waiting.
7. **Cleanup**: the task's terminals and worktrees go; the task folder stays.
   You close the space.

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

- Run `dispatch` inside a herdr-app space on the machine where workers
  should run, so the session is a herdr-core terminal (`HC_TERMINAL_ID` set).
- herdr-core (`hc`) 0.1.21 or newer, `git`, `gh`, `jq`, and a supported agent
  CLI (`claude` by default).
- Linux (`/proc` is used for the capacity check).
- `setup` runs on a macOS laptop with the `coder` CLI logged in, and targets
  Fastly's `gcp-dev-generic` Coder template.

## Credits

`references/grilling.md` is Matt Pocock's
[`grilling`](https://github.com/mattpocock/skills) skill, MIT licensed; see
`skills/dispatch/references/LICENSE-grilling`.
