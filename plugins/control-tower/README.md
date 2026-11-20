# control-tower

Run a Claude session as a **control tower**: a manager of worker agents in
[Herdr](https://herdr.dev) (herdr-app and herdr-core). You hand it a task,
as loose or as thorough as you like; it grills you into one agreed spec,
starts worker agents with small contexts, and presents what they did as one
summary for sign-off.

## Skills

| Skill | Use |
| --- | --- |
| `/control-tower:dispatch [task]` | Hand a task to the tower. |
| `/control-tower:models [harness,...]` | Refresh the models each installed harness (Claude Code, Copilot CLI) offers, for the spec approval page. Run on the workspace. |
| `/control-tower:setup [workspace]` | Set up, check or repair everything the tower needs: the Coder workspace (herdr-core, Claude Code, GitHub auth, Lavish) and the laptop (herdr-app, Coder Connect). Run from your laptop. |

## Flow

Each task gets its own herdr-app space. You create the space, start Claude
in it and run `/control-tower:dispatch`; that session is the task's tower.

1. **Grill**: the tower works out the target repo, then always interviews
   you, scaled to your description: real rounds for a loose idea, a single
   "here is what I understood" round for a thorough one. It runs in your
   browser with [Lavish](https://github.com/kunchenguid/lavish-axi): one
   card per question with the tower's recommendation.
2. **Spec**: one spec for the task, on the same Lavish page: goal, decisions,
   a work split across one or more workers, acceptance criteria, stop
   points. Annotate anything to change, pick each worker's harness (Claude
   Code, Copilot CLI), model and effort, and whether one reviewer follows,
   then press Approve. No worker starts before you approve.
3. **Launch**: `hc run` starts each worker as you picked, named
   `<role>-<slug>`, in a git worktree for coding work or the repo for
   read-only work, with fixed worker rules (draft PRs at most, never merge
   or release). herdr-app lists workers under the tower, without tabs.
4. **Reports**: workers send their report straight to the tower with
   `hc send`; the tower folds each one into the task's `summary.md` as it
   arrives.
5. **Sign-off**: when all workers are done, the tower presents the summary
   in Lavish. With review prep (adapted from Timo Freiberg's
   [`review-prep`](https://github.com/TimoFreiberg/dotfiles/blob/main/agents/skills/review-prep/SKILL.md)),
   one read-only reviewer adds a brief of the change and findings with draft
   comments; you mark each finding, answer the open questions, and sign off,
   ask for a follow-up (a new spec revision), or abandon.
6. **Escalation**: you talk only to the tower. It relays worker prompts to
   you (batched, with a recommendation) and types your answer in; prompts
   you pre-approve go into the spec's Standing yes.
7. **Cleanup**: the task's terminals and worktrees go; the task folder stays.
   You close the space.

Each task in `~/workspace/ai-hub/control-tower/tasks/<date>-<slug>/` holds only
`spec.md` and `summary.md`, plus their Lavish pages (`spec.html`,
`summary.html`).

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
- For grilling, spec approval and sign-off in the browser: `lavish-axi` on the workspace
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
