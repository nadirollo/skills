---
name: setup
description: Use when the user invokes /control-tower:setup to set up, check, or repair the laptop and always-on Coder workspace that control-tower runs on. Creates or reuses a gcp-dev-generic workspace, installs herdr-core, Claude Code, Coder-backed GitHub auth, Lavish and optional tools on it, installs herdr-app and Coder Desktop (Coder Connect) on the laptop, connects the app to the workspace, and installs control-tower. Safe to re-run.
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
| Workspace | Optional: Copilot CLI, aws-cli, Chrome for agent-browser, and Claude Code preferences (status line, longer history). |
| Workspace | The `control-tower` plugin. |
| Laptop | An SSH alias with strict host-key checking. |
| Laptop | herdr-app with the workspace added as a machine. |
| Laptop | Coder Desktop with Coder Connect on, so `http://<ws>.coder:4387` reaches Lavish on the workspace. |

How the pieces fit: herdr-app on the laptop shows spaces, tabs and terminals;
herdr-core on the workspace runs them. The user opens one herdr-app space per
task on the workspace and runs `/control-tower:dispatch` in it. Workers
appear as tabs in that space. Specs are reviewed in the laptop's browser
through Lavish over Coder Connect.

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
  `references/files.md`; never `npx -y` or an unpinned `@latest`.
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

herdr-app connects to the workspace with plain `ssh <ws>`, so this alias is
what it uses.

1. Write `~/.ssh/conf.d/<ws>` from `references/files.md`, and make sure
   `~/.ssh/config` includes `conf.d/*` before any `Host *` block. If it
   doesn't, show the user the line to add and where, and get their OK before
   editing `~/.ssh/config`.
2. If `~/.ssh/known_hosts.<ws>-coder` has no entry, connect once with
   `ssh -o StrictHostKeyChecking=accept-new <ws> true` to record the host
   key, then `chmod 600` the file. The connection runs through the Coder CLI,
   which already authenticates the workspace.
3. If the connection fails with a **changed host key** (common after a
   rebuild), stop and tell the user. Do not delete the entry yourself.
4. Verify: `ssh <ws> hostname` returns the workspace.

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
| Copilot CLI | Latest `copilot-linux-<x64\|arm64>.tar.gz` from `github/copilot-cli` releases into `~/.local/opt/copilot`, plus the `copilot` wrapper from `references/files.md`. |
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

## 8. Claude Code preferences (workspace)

Ask about each; apply only what the user says yes to, merging into the
workspace's `~/.claude/settings.json` with `jq`:

- **Status line** with model, session cost, context use and folder:
  `~/.claude/statusline.sh` and the `statusLine` setting from
  `references/files.md`. If a different `statusLine` is already set, show it
  and ask before replacing it.
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
   `<ws>`, press Cmd+N for a new space on that machine, name it with
   Shift+F2 (e.g. `ct · <task>`), run `claude` in it, then
   `/control-tower:dispatch <task>`.

## 10. Coder Connect (laptop)

1. If Coder Desktop is missing, point the user to Coder's install
   instructions for it (https://coder.com/docs/user-guides/desktop). They
   sign in to the same Coder deployment and turn Coder Connect on
   themselves.
2. Verify the name resolves: `dscacheutil -q host -a name <connect-host>`
   returns an address.
3. Verify Lavish end to end: on the workspace, write a one-line HTML page to
   a scratch folder, open it with the environment from
   `~/.config/control-tower/lavish.env`
   (`set -a; . ~/.config/control-tower/lavish.env; set +a; lavish-axi <page>`),
   then from the laptop `curl -s -o /dev/null -w '%{http_code}' http://<connect-host>:4387/health`
   must print `200`. End the session with `lavish-axi end <page>`, and
   delete the page.

## 11. control-tower (workspace)

1. Find where this plugin came from on the laptop (`claude plugin list`, and
   the marketplace source in `claude plugin marketplace list`).
2. **If that marketplace is a GitHub repo the workspace can reach** (try
   `with-coder-github git ls-remote <repo-url>` on the workspace), add the
   same marketplace there and install `control-tower` from it.
3. **Otherwise** (e.g. a personal repo outside the Fastly orgs, which Coder's
   GitHub credential cannot see), copy the marketplace directory to the
   workspace and add it as a local marketplace. Tell the user that updates
   then need another copy.
4. Create the tasks root, `~/workspace/control-tower/tasks`, if missing.

## 12. Verify and report

Run every check again and report a table:

| Check | How |
| --- | --- |
| Workspace running, no auto-stop | `coder list -o json` |
| SSH alias works | `ssh <ws> hostname` |
| Tools present | `--version` for hc, claude, node, gh, lavish-axi, and each optional tool |
| GitHub auth | `gh auth status` on the workspace |
| Linger on | `loginctl show-user $USER -p Linger` on the workspace |
| Machine reachable from the laptop | `hc machine ls`, `hc exec --on <ws> hostname` |
| Core survives logout | `hc server status` on the workspace: `keeps_running_after_logout: true` |
| Lavish environment | `~/.config/control-tower/lavish.env` names `<connect-host>` |
| Coder Connect reaches Lavish | step 10.3 returned `200` |
| control-tower installed | `claude plugin list` on the workspace |
| Preferences | status line and history setting, if chosen |

For each row give: OK, fixed (and what was done), or needs the user (and the
exact action). End with the logins the user still has to do on the
workspace (model provider, Copilot, GitHub external auth if unlinked) and on
the laptop (Coder Desktop).

## Common repairs

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Machine shows Attention or `needs_login` in herdr-app | SSH failed, or the host key changed after a rebuild | Check `ssh <ws> true`; for a changed key, confirm with the user it was rebuilt, then replace the entry in `~/.ssh/known_hosts.<ws>-coder`; then `hc machine login <ws>` |
| Terminals gone after logging out | Linger off | Step 4.2 |
| Terminals restarted as fresh shells | The workspace rebooted or the core was restarted | Expected: kept terminals get fresh shells, not their old programs |
| Lavish link does not load | Coder Connect off, or Lavish not running | Turn on Coder Connect; the tower reopens the session |
| Lavish page loads but annotation does nothing | Opened through the Coder port-share URL | Use the `http://<connect-host>:4387/...` link |
| Lavish answers `forbidden host` | `lavish.env` names a different host than the link | Fix `lavish.env` (step 7.2); a tower restarts Lavish only when no other task has a review open |
| `gh` or `git push` fails with 401 or 403 in a long-lived terminal | Token exported at shell start expired | Use the `gh` wrapper and git credential helper, step 3.2 |
| `403` cloning a personal repo | Coder's GitHub credential covers only the orgs its app is installed on | Expected; use a laptop checkout or a separate credential |
| Claude can't reach the model | Provider login expired | Log in again on the workspace (step 6.3) |

## Anti-patterns (DO NOT)

- Creating, rebuilding or resizing a workspace without explicit confirmation.
- Copying tokens, SSO caches, API keys or credential files to the workspace.
- Stopping, restarting or replacing a running hc core without the user's OK.
- Approving an hc copy or replace prompt during `hc machine add`.
- Deleting a known-hosts entry because a host key changed, without the user.
- Passing build parameters with `--parameter` when their names contain spaces.
- Installing Lavish unpinned, with install scripts, or through `npx -y`.
- Exposing Lavish through the Coder port-share URL or a public port.
- Reporting a step as done without its verification.
