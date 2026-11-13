---
name: setup
description: Use when the user invokes /control-tower:setup to set up, check, or repair the laptop and always-on Coder workspace that control-tower runs on. Creates or reuses a gcp-dev-generic workspace, installs herdr-core, Claude Code (agents run without permission prompts), Coder-backed GitHub auth, Lavish, the Fastly agent skills and optional tools on it, installs herdr-app and Coder Desktop (Coder Connect) on the laptop, connects the app to the workspace, and installs control-tower. Safe to re-run.
argument-hint: "[workspace-name]"
disable-model-invocation: true
---

# Setup

Set up an always-on Coder workspace where control-tower and its workers run,
and connect it to the user's laptop. Run from the **laptop** (macOS): it
configures both sides.

Workspace name from the user: $ARGUMENTS

## End state

| Side | Result |
| --- | --- |
| Coder | A running `gcp-dev-generic` workspace with no auto-stop. |
| Workspace | herdr-core (`hc`), with linger on so terminals survive logout. |
| Workspace | Claude Code, Node, GitHub auth through Coder, and Claude model settings mirrored from the laptop; the user logs in themselves. |
| Workspace | Lavish (`lavish-axi`, pinned) and its control-tower environment file, for spec review in the browser. |
| Workspace | Agents run without permission prompts: Claude Code in `bypassPermissions` mode, Copilot with `--yolo`. The workspace is the safe environment for that. |
| Workspace | Claude Code and Copilot trust every folder (`/`), so no session stops at a folder-trust prompt. |
| Workspace | `~/.config/control-tower/models.json`: the models each harness offers, for dispatch's spec approval page. |
| Workspace | Optional: Copilot CLI, aws-cli, Chrome for agent-browser, and Claude Code preferences (status line, longer history). |
| Workspace | The `control-tower` plugin and the Fastly agent skills (`coding` at least), both from GitHub. |
| Laptop | An SSH alias for the workspace. Setup checks it and suggests one if missing; the user writes it. |
| Laptop | herdr-app with the workspace added as a machine. |
| Laptop | Coder Desktop with Coder Connect on, so `http://<ws>.coder:4387` reaches Lavish on the workspace. |

How the pieces fit: herdr-app on the laptop shows spaces, tabs and terminals;
herdr-core on the workspace runs them. The user opens one herdr-app space per
task on the workspace and runs `/control-tower:dispatch` in it. Workers
appear under the tower in herdr-app's agents panel, not as tabs. Specs are
reviewed in the laptop's browser through Lavish over Coder Connect.

## Ground rules

- **Check before acting.** Every step first checks the current state, changes
  only what is missing or wrong, then verifies. On a re-run, the skill doubles
  as a repair tool.
- **Confirm before anything that costs money or is hard to undo:** creating
  the workspace, rebuilding it, or changing its parameters.
- **Never copy credentials** to the workspace: no tokens, API keys, SSO
  caches, SSH private keys, or `~/.claude/.credentials.json`. The user logs in
  on the workspace.
- **Never stop, restart or replace a running hc core** without the user's
  OK. It would end or restart every terminal and agent on it.
- **Overwrite nothing silently.** Back up a differing file as
  `<file>.bak-<YYYYMMDD>` before replacing it, and report it.
- **Pin and verify third-party tools.** Use the versions and installers in
  `references/files.md`; never `npx -y` or an unpinned `@latest`. The one
  exception is Copilot CLI, which is installed at its latest release.
- **Never edit the user's SSH configuration** (`~/.ssh/config`,
  `~/.ssh/conf.d/`, known-hosts files). Check it, and if something is
  missing, show the user what to add and let them do it.
- **Global agent instructions are personal.** Do not write
  `~/.claude/CLAUDE.md`, `~/.claude/rules/`, `AGENTS.md` or Copilot
  instructions on either side. Suggest that the user write their own
  (step 12).
- The exact file contents are in `references/files.md`. Use them as written.
- Run workspace commands as `ssh <ws> '<command>'` once the alias exists, or
  `coder ssh <ws> -- <command>` before that. Start workspace commands with
  `export PATH=$HOME/.local/bin:$PATH`.

## 0. Preflight (laptop)

1. macOS laptop; `coder` installed and logged in (`coder whoami`). If not
   logged in, ask the user to run `coder login <url>` themselves.
2. Compare client and server versions: `coder version` against
   `curl -fsSL <coder-url>/api/v2/buildinfo | jq -r .version`. If the minor
   versions differ, tell the user to upgrade the CLI (e.g.
   `brew upgrade coder`) before continuing: older clients can silently drop
   build parameters whose names contain spaces.
3. herdr-app: look for `~/Applications/Herdr.app` or `/Applications/Herdr.app`,
   and `herdr-app` and `hc` on `PATH` (`~/.local/bin`). Record their versions.
4. Coder Desktop: look for it in `/Applications`, and whether Coder Connect is
   on (the user can see it in the menu bar app).
5. Record what you find. Do not change anything yet.

## 1. Coder workspace

1. Ask for the workspace name if `$ARGUMENTS` is empty, defaulting to
   `ai-hub`. Check `coder list -o json`.
2. **If it exists:** read its parameters (`coder state pull <ws>`, the
   `coder_parameter` resources) and its schedule. Report anything below the
   recommendation (machine type, disk) but do not change it unless the user
   asks.
3. **If it does not exist,** offer to create it. Read the active
   `gcp-dev-generic` version's parameters live (Coder MCP
   `coder_template_version_parameters`, or the template page in the
   dashboard); do not rely on remembered option lists. Propose:

   | Parameter | Proposal |
   | --- | --- |
   | Budget Owner | Ask; required, no default. |
   | Region | Closest to the user. **Cannot be changed later.** |
   | Machine Type | `n2-standard-8` (8 vCPU, 32 GB): room for about 10 workers. |
   | Disk Size | 250 GB |
   | IDEs, Fastly features | As the user wants. |

   Show the full list with the monthly cost from the template, and create
   only after explicit confirmation. Pass parameters with a YAML file
   (`coder create <ws> --template gcp-dev-generic --rich-parameter-file <file> --yes`),
   not `--parameter` flags: names with spaces break their parsing.
4. Turn off auto-stop: `coder schedule stop <ws> manual`. The point of the
   workspace is that it never sleeps; say so and confirm, since it keeps
   costs running.
5. Wait for the workspace to be running and its agent connected.

## 2. SSH alias (laptop)

herdr-app connects to the workspace with plain `ssh <ws>`, so it needs a
`Host <ws>` entry that reaches the workspace. This step only checks and
suggests: **do not edit any SSH file yourself.**

1. Check: `ssh -G <ws>` shows a `proxycommand` that runs `coder ssh`, and
   `ssh <ws> hostname` returns the workspace. Note what `ssh -G` reports for
   `user`, `controlmaster` and `stricthostkeychecking`.
2. **If it works,** leave it as it is, even if it differs from the
   suggestion. Mention any difference worth knowing (for example no
   connection reuse) as a suggestion only.
3. **If there is no working entry,** show the user the suggested
   `~/.ssh/conf.d/<ws>` from `references/files.md` (filled in), the
   `Include conf.d/*` line and where it must go in `~/.ssh/config` (before
   any `Host *` block), and the one-time command that records the host key.
   Wait until they say it is done, then check again.
4. If the connection fails with a **changed host key** (common after a
   rebuild), stop and tell the user. Do not touch the known-hosts entry.
5. Until the alias works, run workspace commands with
   `coder ssh <ws> -- <command>`. Steps 9 and later need the alias.

## 3. Workspace base

1. Shell setup and `~/.local/bin`, `~/.local/opt`, `~/workspace`
   directories, from `references/files.md`.
2. The server's own Coder CLI at `~/.local/bin/coder`, the
   `with-coder-github` and `gh` wrappers, and the git credential helper.
   Verify with `ssh <ws> '~/.local/bin/gh auth status'`. If Coder reports that
   GitHub external auth isn't linked, give the user the link to connect it in
   the Coder dashboard.
3. `~/.config/environment.d/git.conf` from `references/files.md`.
4. **Node** (required by Lavish): current LTS from nodejs.org, unpacked in
   `~/.local/opt/node-<version>-linux-<arch>`, with `node`, `npm` and `npx`
   symlinked into `~/.local/bin`.
5. **Claude Code:** `curl -fsSL https://claude.ai/install.sh | bash`. Verify
   `claude --version`. Claude Code reports its status to hc itself; no hook
   is needed.

## 4. herdr-core (workspace)

1. If `hc --version` fails, install it with the herdr-core installer from
   `references/files.md`. If it is present, leave it: herdr-app updates it
   when the user approves an update in the app.
2. Linger: check `loginctl show-user "$USER" -p Linger`. If it is `no`, run
   `sudo loginctl enable-linger "$USER"`. Without it, every terminal ends
   when the user's last login closes.
3. **If an hc core is already running** (`hc server status`), do not restart
   it.
4. Verify: `hc --version` works, and once herdr-app has connected (step 9),
   `hc server status` reports `keeps_running_after_logout: true`.

## 5. Optional tools (workspace)

Ask which the user wants, then install each into `~/.local`:

| Tool | Install |
| --- | --- |
| Copilot CLI | The latest `copilot-linux-<x64\|arm64>.tar.gz` from the `github/copilot-cli` releases (`gh release view --repo github/copilot-cli`), unpacked into `~/.local/opt/copilot`, plus the `copilot` wrapper from `references/files.md` (GitHub auth through Coder, and `--yolo`). On a re-run, replace it if a newer release exists. |
| aws-cli | `awscli-exe-linux-<x86_64\|aarch64>.zip` from awscli.amazonaws.com, installed with `./aws/install -i ~/.local/share/aws-cli -b ~/.local/bin`. Needed for Bedrock. |
| Chrome for agent-browser | `npm install -g agent-browser`, then `agent-browser install --with-deps` (Chrome for Testing and its system libraries; needs `sudo`). |

Verify each with `--version`.

## 6. Model access (workspace)

1. Read the laptop's `~/.claude/settings.json` and copy only the allowed
   model keys listed in `references/files.md`. Show the user exactly what
   will be copied before writing.
2. For Bedrock, copy the matching `~/.aws/config` profile and `sso-session`
   blocks, and make sure aws-cli is installed (offer it from step 5).
3. Tell the user how to log in on the workspace, e.g.
   `ssh <ws>` then `aws sso login --profile <profile> --use-device-code --no-browser`,
   and that Claude Code needs it before any session can reach the model.

## 7. Lavish (workspace)

1. If `lavish-axi --version` is not the pinned version in
   `references/files.md`, install that version as written there (npm, install
   scripts off, telemetry off) and link it into `~/.local/bin`.
2. Work out the Coder Connect name: `<ws>.coder`, unless the user's Coder
   Desktop shows a different suffix. Write
   `~/.config/control-tower/lavish.env` from `references/files.md` with that
   name.
3. Verify end to end once Coder Connect is on (step 10).

## 8. Claude Code settings (workspace)

Merge into the workspace's `~/.claude/settings.json` with `jq`; never replace
the file.

1. **Agent permissions (recommended).** The workspace is a disposable,
   single-user VM that holds no credentials beyond the user's own logins, so
   agents on it run without permission prompts: workers then block only on
   real questions, not on every command. Set the keys in
   `references/files.md` (`permissions.defaultMode: "bypassPermissions"`,
   `skipDangerousModePermissionPrompt: true`). Explain this to the user and
   apply it after their OK. Keep any existing `permissions.allow` and
   `permissions.deny` entries. The dispatch worker rules (no merges,
   releases, deploys or infrastructure applies) still apply; they come from
   the worker prompt, not from permission prompts.
2. **Folder trust (recommended, with 8.1).** For the same reason, Claude
   Code and Copilot trust every folder on the workspace, so a worker started
   in a new worktree or scratch folder never stops at a trust prompt. Both
   treat a trusted folder's subfolders as trusted, so trusting `/` covers
   everything. Explain it with 8.1 and apply it after the user's OK, on the
   workspace only:
   Let each harness record it itself, at its own trust question: never edit
   `~/.claude.json` (every running Claude session rewrites it) or
   `~/.copilot/config.json` (Copilot manages it, and it starts with comment
   lines that `jq` cannot parse). Start both in `/` in hidden hc terminals,
   read each screen before pressing anything, answer, then end them:

   ```bash
   hc run --bg --json --no-parent --no-notify --name ct-trust-claude --cwd / claude
   hc run --bg --json --no-parent --no-notify --name ct-trust-copilot --cwd / copilot
   hc read ct-trust-claude --lines 0    # must ask to trust "/", cursor on "No, exit"
   hc read ct-trust-copilot --lines 0   # must ask to trust "/", cursor on "1. Yes"
   hc keys ct-trust-claude down enter   # "Yes, I trust this folder"
   hc keys ct-trust-copilot down enter  # "2. Yes, and remember this folder for future sessions"
   hc read ct-trust-claude --lines 0    # the question is gone (same for copilot)
   hc kill ct-trust-claude; hc kill ct-trust-copilot
   hc rm ct-trust-claude; hc rm ct-trust-copilot
   ```

   - A harness that shows no question already trusts `/`. A screen that
     shows anything else (a login, a different question, other options):
     stop and show it to the user; never press keys on a guess.
   - It is recorded as `projects["/"].hasTrustDialogAccepted: true` in
     `~/.claude.json`, and `/` in Copilot's `trustedFolders` (`copilot help
     config`). Read them to confirm; Copilot's file needs its leading `//`
     lines dropped before `jq`.
   - **Verify** each: start it in a new folder outside your home
     (`mktemp -d /var/tmp/ct-trust.XXXXXX`) the same way and check no trust
     question shows: Claude reaches its prompt, Copilot its input box (it
     may still be loading MCP servers). End them and remove the folder. If
     a harness still asks there, trust `$HOME` and `/tmp` the same way
     instead and tell the user that folders elsewhere will still ask.
3. **Preferences.** Ask about each; apply only what the user says yes to:

   - **Status line** with model, session cost, context use and folder:
     `~/.claude/statusline.sh` and the `statusLine` setting from
     `references/files.md`. If a different `statusLine` is already set, show
     it and ask before replacing it.
   - **Keep session history for a year:** `"cleanupPeriodDays": 365`. The
     default is 30 days.

## 9. herdr-app (laptop)

1. If herdr-app is missing, offer to install it:
   `brew install --cask herdr-app`, or the official installer
   (`curl -fsSL https://releases.herdr.dev/app/install.sh | sh`). Either also
   installs herdr-core on the laptop if it has none. If `hc --version` still
   fails on the laptop afterwards, install it with the herdr-core installer
   from `references/files.md`.
2. Tell the user herdr-app sends usage telemetry by default, and where to
   turn it off (Settings → Privacy). Let them decide.
3. If the workspace is not yet a machine (`hc machine ls` on the laptop),
   add it under the workspace's name: `hc machine add <ws> --name <ws>`, or
   from the app (Settings → Machines, then pick `<ws>` from the SSH hosts).
   If it offers to copy or replace hc on the workspace, stop: step 4 should
   have installed it, so a prompt means something is wrong. Answer No and
   investigate.
4. Verify: `hc machine ls` shows `<ws>` reachable, without `needs_login` or
   `! stops at logout`, and `hc exec --on <ws> hostname` returns the
   workspace.
5. Show the user how to start a task: in herdr-app, select a space on
   `<ws>`, press Cmd+N for a new space on that machine, run `claude` in
   it, then `/control-tower:dispatch <task>`. The tower names the space
   after the task itself.

## 10. Coder Connect (laptop)

1. If Coder Desktop is missing, offer to install it with
   `brew install --cask coder-desktop` (Coder's instructions:
   https://coder.com/docs/user-guides/desktop). The user then signs in to
   the same Coder deployment and turns Coder Connect on themselves; macOS
   asks them to allow its network extension.
2. Verify the name resolves: `dscacheutil -q host -a name <connect-host>`
   returns an address.
3. Verify Lavish end to end: on the workspace, write a one-line HTML page to
   a scratch folder, open it with the environment from
   `~/.config/control-tower/lavish.env`
   (`set -a; . ~/.config/control-tower/lavish.env; set +a; lavish-axi <page>`),
   then from the laptop `curl -s -o /dev/null -w '%{http_code}' http://<connect-host>:4387/health`
   must print `200`. End the session with `lavish-axi end <page>`, and
   delete the page.

## 11. Plugins (workspace)

Install both marketplaces from GitHub, so the workspace updates with
`claude plugin marketplace update` and never needs a copy from the laptop.

1. **control-tower.** Its marketplace is the public `nadirollo/skills` repo:

   ```bash
   claude plugin marketplace add nadirollo/skills
   claude plugin install control-tower@nadirollo-skills --scope user
   ```

   If `nadirollo-skills` is already there with another source (a folder, a
   copy), show the user and, with their OK, switch it:
   `claude plugin marketplace remove nadirollo-skills`, then the two commands
   above. Leave the old folder in place.
2. **Fastly agent skills.** The `fastly/agent-skills-internal` repo is
   internal; the git credential helper from step 3.2 gives the workspace
   access. Add it as the `fastly-agent-skills-internal` marketplace:

   ```bash
   claude plugin marketplace add fastly/agent-skills-internal
   claude plugin install coding@fastly-agent-skills-internal --scope user
   ```

   `coding` provides the `coding:code-review` skill that dispatch's review
   workers use. Then show the user the other plugins installed from that
   marketplace on the laptop (`claude plugin list`) and install the ones
   they pick, with `--scope user`.
3. Create the tasks root, `~/workspace/control-tower/tasks`, if missing.
4. **Model list.** Write `~/.config/control-tower/models.json`, which the
   dispatch spec page loads into its model dropdowns, by running the
   `models` skill's probe on the workspace (about a minute; it sends nothing
   to a model):

   ```bash
   ssh <ws> 'export PATH=$HOME/.local/bin:$PATH
     python3 -I "$(ls -d ~/.claude/plugins/cache/*/control-tower/*/skills/models/scripts/probe_models.py | sort -V | tail -1)"'
   ```

   It reports the number of models per harness. A harness that is not
   logged in yet can fail: say which, and tell the user to run
   `/control-tower:models` in a workspace Claude session after logging in.
   On a re-run, run it again: it refreshes the list.

## 12. Verify and report

Run every check again and report a table:

| Check | How |
| --- | --- |
| Workspace running, no auto-stop | `coder list -o json` |
| SSH alias works | `ssh <ws> hostname`; if not, the suggestion from step 2 |
| Tools present | `--version` for hc, claude, node, gh, lavish-axi, and each optional tool |
| GitHub auth | `gh auth status` on the workspace |
| Linger on | `loginctl show-user $USER -p Linger` on the workspace |
| Machine reachable from the laptop | `hc machine ls`, `hc exec --on <ws> hostname` |
| Core survives logout | `hc server status` on the workspace: `keeps_running_after_logout: true` |
| Lavish environment | `~/.config/control-tower/lavish.env` names `<connect-host>` |
| Coder Connect reaches Lavish | step 10.3 returned `200` |
| control-tower installed | `claude plugin list` on the workspace, and `claude plugin marketplace list` shows `nadirollo-skills` from GitHub |
| Agents run without prompts | workspace `~/.claude/settings.json` has `permissions.defaultMode: "bypassPermissions"` and `skipDangerousModePermissionPrompt: true`; the `copilot` wrapper passes `--yolo` |
| Fastly agent skills | `claude plugin list` on the workspace shows `coding@fastly-agent-skills-internal` and the plugins the user picked |
| Folder trust | step 8.2's check: Claude and Copilot start in a new folder under `/var/tmp` without a trust question |
| Model list | `~/.config/control-tower/models.json` on the workspace lists every installed harness, none `stale` |
| Preferences | status line and history setting, if chosen |

For each row give: OK, fixed (and what was done), or needs the user (and the
exact action). End with the logins the user still has to do on the
workspace (model provider, Copilot, GitHub external auth if unlinked) and on
the laptop (Coder Desktop).

Finally, suggest, without writing anything, that the user keep their own
global agent instructions on the workspace: `~/.claude/CLAUDE.md` for Claude
Code (and `~/.copilot/copilot-instructions.md` for Copilot), with how they
like agents to work, for example how terse to be, or that every merge needs
their explicit approval. These are personal, so setup does not create
them.

## Common repairs

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Machine shows Attention or `needs_login` in herdr-app | SSH failed, or the host key changed after a rebuild | Check `ssh <ws> true`; for a changed key, confirm with the user it was rebuilt and ask them to replace its known-hosts entry; then `hc machine login <ws>` |
| Terminals gone after logging out | Linger off | Step 4.2 |
| Terminals restarted as fresh shells | The workspace rebooted or the core was restarted | Expected: kept terminals get fresh shells, not their old programs |
| Lavish link does not load | Coder Connect off, or Lavish not running | Turn on Coder Connect; the tower reopens the session |
| Lavish page loads but annotation does nothing | Opened through the Coder port-share URL | Use the `http://<connect-host>:4387/...` link |
| Lavish answers `forbidden host` | `lavish.env` names a different host than the link | Fix `lavish.env` (step 7.2); a tower restarts Lavish only when no other task has a review open |
| `gh` or `git push` fails with 401 or 403 in a long-lived terminal | Token exported at shell start expired | Use the `gh` wrapper and git credential helper, step 3.2 |
| `403` cloning a personal repo | Coder's GitHub credential covers only the orgs its app is installed on | Expected; use a laptop checkout or a separate credential |
| Claude can't reach the model | Provider login expired | Log in again on the workspace (step 6.3) |
| Workers stop at permission prompts for every command | Agent permissions not set | Step 8.1 |
| A worker stops at "trust this folder" | Folder trust not set | Step 8.2 |
| The spec page offers only a few models, or says the list is missing | `models.json` missing or old | Step 11.4, or `/control-tower:models` on the workspace |

## Anti-patterns (DO NOT)

- Creating, rebuilding or resizing a workspace without explicit confirmation.
- Copying tokens, SSO caches, API keys or credential files to the workspace.
- Stopping, restarting or replacing a running hc core without the user's OK.
- Approving an hc copy or replace prompt during `hc machine add`.
- Editing `~/.ssh/config`, `~/.ssh/conf.d/` or any known-hosts file. Suggest; the user edits.
- Writing global agent instructions (`~/.claude/CLAUDE.md`, rules, `AGENTS.md`) for the user.
- Copying a marketplace to the workspace when it can be added from GitHub.
- Trusting `/` (or any folder) for Claude Code or Copilot on the laptop, or
  editing `~/.claude.json` by hand.
- Passing build parameters with `--parameter` when their names contain spaces.
- Installing Lavish unpinned, with install scripts, or through `npx -y`.
- Exposing Lavish through the Coder port-share URL or a public port.
- Reporting a step as done without its verification.
