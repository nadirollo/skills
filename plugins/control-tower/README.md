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
| `/control-tower:models [harness,...]` | Refresh the models each installed harness (Claude Code, Copilot CLI) offers, for the spec approval page. Run on the workspace. |
| `/control-tower:setup [workspace]` | Set up, check or repair everything the tower needs: the Coder workspace (herdr-core, Claude Code, GitHub auth, Lavish) and the laptop (herdr-app, Coder Connect). Run from your laptop. |

## Flow

Each task gets its own herdr-app space. You create the space, start Claude
in it and run `/control-tower:dispatch`; that session is the task's tower.

1. **Intake**: the tower names an unnamed space after the task (2–3 words), works
   out the target repo, and asks whether you want a grilling interview
   first. The grilling runs in your browser with
   [Lavish](https://github.com/kunchenguid/lavish-axi): one card per
   question with the tower's recommendation; answer them one by one, ask
   about any of them, and send the round.
2. **Spec**: written from the grilling or straight from your description.
   You review it in Lavish, on the same page as the grilling if there was
   one: annotate anything to change, pick the worker's
   harness (Claude Code, Copilot CLI), model and effort from dropdowns, and
   whether a review prep follows, then press Approve. No worker starts until
   you approve its spec. Without Lavish, all of this happens in the chat.
3. **Launch**: `hc run` starts each worker agent with the harness, model and effort you picked,
   named `<role>-<slug>`, in a git worktree for coding work or the repo for
   read-only work, with a fixed set of worker rules (draft PRs at most, never
   merge or release). Workers are the tower's hc children: herdr-app lists
   them under the tower in its agents panel, without opening tabs.
4. **Watch**: a background `hc wait --children any`; workers report with
   `hc send`, and the tower reads each worker's `report.md`.
5. **Sign-off**: when a worker is done, the tower presents its report in
   Lavish. With review prep (adapted from Timo Freiberg's
   [`review-prep`](https://github.com/TimoFreiberg/dotfiles/blob/main/agents/skills/review-prep/SKILL.md)),
   read-only reviewers add a brief of the change and findings by severity
   with draft comments; you mark each finding, answer the questions before
   sign-off, and choose the next step.
6. **Follow-ups**: fixes for findings, CI and PR-comment workers, each with
   its own spec, in the same space.
7. **Escalation**: you talk only to the tower. It relays every worker prompt
   or question to you in its own chat (batched, with a recommendation) and
   types your answer into the worker; prompt classes you delegate for the
   task it answers itself and logs. It also asks you for decisions, expired
   logins and merge approvals; herdr-app shows it waiting.
8. **Cleanup**: the task's terminals and worktrees go; the task folder stays.
   You close the space.

Task records live in `~/workspace/control-tower/tasks/<date>-<slug>/`
(`log.md`, `grilling.html`, `spec.md`/`spec.html`, `report.md`/`report.html`,
`followups/`).

## Install

1. Get the plugin on your laptop. From GitHub (needs access to the private
   repo):

   ```text
   /plugin install control-tower --marketplace nadirollo/skills
   ```

   Or from a local checkout:

   ```bash
   claude plugin marketplace add <path-to-checkout>
   claude plugin install control-tower@nadirollo-skills --scope user
   ```

2. On the laptop, run `/control-tower:setup [workspace-name]`. It creates or
   repairs the Coder workspace, installs everything on both sides, and
   installs the plugin on the workspace too. It is safe to re-run as a
   repair tool.
3. Log in where setup tells you (model provider on the workspace, Coder
   Desktop on the laptop).

Then, for each task: in herdr-app, open a new space on the workspace
(Cmd+N while a workspace space is selected), name it, run `claude`, and
`/control-tower:dispatch <task>`.

## Requirements

- Run `dispatch` inside a herdr-app space on the machine where workers
  should run, so the session is a herdr-core terminal (`HC_TERMINAL_ID` set).
- herdr-core (`hc`) 0.1.21 or newer, `git`, `gh`, `jq`, and a supported agent
  CLI: `claude` and `copilot` today (see `skills/dispatch/references/harnesses.md`
  to add one).
- Optional, for grilling, spec review and report sign-off in the browser: `lavish-axi` on the workspace
  (tested with 0.1.96), and Coder Connect (Coder Desktop) on the laptop, so
  `http://ai-hub.coder:4387` reaches it. Not the Coder port-share URL: its
  login proxy breaks Lavish's annotations.
- Linux (`/proc` is used for the capacity check).
- `setup` runs on a macOS laptop with the `coder` CLI logged in, and targets
  Fastly's `gcp-dev-generic` Coder template.

## Credits

`references/grilling.md` is Matt Pocock's
[`grilling`](https://github.com/mattpocock/skills) skill, MIT licensed; see
`skills/dispatch/references/LICENSE-grilling`.
