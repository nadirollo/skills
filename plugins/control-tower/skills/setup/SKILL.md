---
name: setup
description: Use when the user invokes /control-tower:setup to set up, check, or repair an always-on Coder workspace for Herdr and control-tower from their laptop. Creates or reuses a gcp-dev-generic workspace, installs Herdr as a persistent service with its plugins, Claude Code, Coder-backed GitHub auth and optional tools, connects it to the laptop's Herdr as a saved SSH machine, and installs control-tower with a ControlTower workspace. Safe to re-run.
argument-hint: "[workspace-name]"
disable-model-invocation: true
---

# Setup

Set up an always-on Coder workspace where Herdr and control-tower run, and
connect it to the user's laptop Herdr window. Run from the **laptop** (macOS):
it configures both sides.

Workspace name from the user: $ARGUMENTS

## End state

| Side | Result |
| --- | --- |
| Coder | A running `gcp-dev-generic` workspace with no auto-stop. |
| Workspace | Herdr running as a systemd user service that survives logout, reboot and crashes. |
| Workspace | Claude Code, Node, GitHub auth through Coder, the Herdr Radar and Bar plugins, and the Herdr hooks for each agent CLI. |
| Workspace | Optional: Copilot CLI, aws-cli, Chrome for agent-browser. |
| Workspace | Claude model settings mirrored from the laptop; the user logs in themselves. |
| Workspace | The `control-tower` plugin and a `ControlTower` Herdr workspace. |
| Laptop | An SSH alias with strict host-key checking, and the workspace saved as a Herdr machine. |

## Ground rules

- **Check before acting.** Every step first checks the current state, changes
  only what is missing or wrong, then verifies. On a re-run, the skill doubles
  as a repair tool.
- **Confirm before anything that costs money or is hard to undo:** creating
  the workspace, rebuilding it, or changing its parameters.
- **Never copy credentials** to the workspace: no tokens, API keys, SSO
  caches, SSH private keys, or `~/.claude/.credentials.json`. The user logs in
  on the workspace.
- **Never stop or replace a running Herdr server** without the user's OK. It
  would kill every pane and agent on it.
- **Overwrite nothing silently.** Back up a differing file as
  `<file>.bak-<YYYYMMDD>` before replacing it, and report it.
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
3. `herdr` on the laptop: if missing, offer to install it with
   `curl -fsSL https://herdr.dev/install.sh | sh`. If present, run
   `herdr status`.
4. Record what you find. Do not change anything yet.

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
3. **Node** (required by Radar): current LTS from nodejs.org, unpacked in
   `~/.local/opt/node-<version>-linux-<arch>`, with `node`, `npm` and `npx`
   symlinked into `~/.local/bin`.
4. **Claude Code:** `curl -fsSL https://claude.ai/install.sh | bash`. Verify
   `claude --version`.
5. **Herdr:** `curl -fsSL https://herdr.dev/install.sh | sh`. Verify
   `herdr --version`. Compare it with the laptop's: if their protocol
   versions differ (`herdr status` on each side), update the older side
   first.

## 4. Herdr service (workspace)

1. Write `~/.config/environment.d/git.conf` and
   `~/.config/systemd/user/herdr.service` from `references/files.md`. Use the
   workspace's own `CODER_URL` (`printenv CODER_URL` in a workspace session).
2. Enable linger, reload, then enable and start the service.
3. **If a Herdr server is already running outside systemd** (for example
   started by an earlier `herdr machine add`): tell the user that moving it
   under systemd restarts it and closes its panes, and ask before stopping
   it.
4. Verify: `systemctl --user is-active herdr` is `active`, and `herdr status`
   reports a running server.

## 5. Herdr plugins and hooks (workspace)

1. Install the plugins through the GitHub wrapper, since installs clone from
   GitHub:

   ```bash
   with-coder-github herdr plugin install hhdebb/herdr-radar --yes
   with-coder-github herdr plugin install jeffarese/herdr-bar --yes
   ```

2. **Start Radar's state service:**
   `herdr plugin action invoke hhdebb.herdr-radar.state-start`. Without it,
   the laptop's Radar sidebar shows this machine's workspaces and agents as
   blank rows. Herdr draws the sidebar from the laptop's settings, and only
   Radar running on the workspace fills in the names. Verify with
   `herdr workspace list`: each workspace must have `tokens.space_label`.
3. Install the Herdr hook for each agent CLI on the workspace:
   `herdr integration install claude`, plus `herdr integration install copilot`
   if Copilot is chosen.

## 6. Optional tools (workspace)

Ask which the user wants, then install each into `~/.local`:

| Tool | Install |
| --- | --- |
| Copilot CLI | Latest `copilot-linux-<x64\|arm64>.tar.gz` from `github/copilot-cli` releases into `~/.local/opt/copilot`, plus the `copilot` wrapper from `references/files.md`. |
| aws-cli | `awscli-exe-linux-<x86_64\|aarch64>.zip` from awscli.amazonaws.com, installed with `./aws/install -i ~/.local/share/aws-cli -b ~/.local/bin`. |
| Chrome for agent-browser | `npm install -g agent-browser`, then `agent-browser install --with-deps` (Chrome for Testing and its system libraries; needs `sudo`). |

Verify each with `--version`.

## 7. Model access (workspace)

1. Read the laptop's `~/.claude/settings.json` and copy only the allowed
   model keys listed in `references/files.md`. Show the user exactly what
   will be copied before writing.
2. For Bedrock, copy the matching `~/.aws/config` profile and `sso-session`
   blocks, and make sure aws-cli is installed (offer it from step 6).
3. Tell the user how to log in on the workspace, e.g.
   `ssh <ws>` then `aws sso login --profile <profile> --use-device-code --no-browser`,
   and that Claude Code needs it before any session can reach the model.

## 8. Laptop Herdr

1. Check whether the laptop's sidebar uses Radar (`~/.config/herdr/config.toml`
   contains Radar's managed blocks or `$space_label` tokens). If it does, step
   5's Radar setup is required; say so in the report.
2. If the workspace is not yet a saved machine (`herdr machine list --json`),
   add it: `herdr machine add <ws> --label <ws> --remote-session default`. If
   it asks to install or replace anything on the workspace, stop: steps 3–4
   should already have handled that, so a prompt means something is wrong.
   Answer No (the default) and investigate.
3. Verify: `herdr machine status <ws> --json` reports `reachable`, and
   `herdr --machine <ws> workspace list` returns the workspaces.

## 9. control-tower (workspace)

1. Find where this plugin came from on the laptop (`claude plugin list`, and
   the marketplace source in `claude plugin marketplace list`).
2. **If that marketplace is a GitHub repo the workspace can reach** (try
   `with-coder-github git ls-remote <repo-url>` on the workspace), add the
   same marketplace there and install `control-tower` from it.
3. **Otherwise** (e.g. a personal repo outside the Fastly orgs, which Coder's
   GitHub credential cannot see), copy the marketplace directory to the
   workspace and add it as a local marketplace. Tell the user that updates
   then need another copy.
4. Create a `ControlTower` Herdr workspace on the workspace if missing:
   `herdr --machine <ws> workspace create --cwd /home/<coder-user> --label ControlTower --no-focus`.
   Use an absolute path; `~` is not expanded.
5. Ask about personal preferences, applied only if the user says yes:
   - Keep Claude session history for a year: `"cleanupPeriodDays": 365` in
     the workspace's `~/.claude/settings.json`. The default is 30 days.

## 10. Verify and report

Run every check again and report a table:

| Check | How |
| --- | --- |
| Workspace running, no auto-stop | `coder list -o json` |
| SSH alias works | `ssh <ws> hostname` |
| Herdr service active, enabled, linger on | `systemctl --user is-active herdr`, `is-enabled`, `loginctl show-user $USER -p Linger` |
| Tools present | `--version` for herdr, claude, node, gh, and each optional tool |
| GitHub auth | `gh auth status` |
| Radar names filled | `herdr workspace list` shows `tokens.space_label` |
| Herdr hooks installed | `~/.claude/hooks/herdr-agent-state.sh` exists |
| Saved machine reachable | `herdr machine status <ws> --json` |
| control-tower installed | `claude plugin list` on the workspace |
| ControlTower workspace exists | `herdr --machine <ws> workspace list` |

For each row give: OK, fixed (and what was done), or needs the user (and the
exact action). End with the logins the user still has to do on the
workspace (model provider, Copilot, GitHub external auth if unlinked).

## Common repairs

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Workspace rows blank in the laptop sidebar | Radar's state service not running on the workspace (e.g. after a reboot) | Step 5.2 |
| Machine shows Attention after a workspace rebuild | Host key changed | Confirm with the user it was rebuilt, then replace the entry in `~/.ssh/known_hosts.<ws>-coder` |
| Panes gone after a reboot | Service not enabled, or linger off | Step 4 |
| `gh` or `git push` fails with 401 or 403 in a long-lived pane | Token exported at shell start expired | Use the `gh` wrapper and git credential helper, step 3.2 |
| `403` cloning a personal repo | Coder's GitHub credential covers only the orgs its app is installed on | Expected; use a laptop checkout or a separate credential |
| Claude can't reach the model | Provider login expired | Log in again on the workspace (step 7.3) |

## Anti-patterns (DO NOT)

- Creating, rebuilding or resizing a workspace without explicit confirmation.
- Copying tokens, SSO caches, API keys or credential files to the workspace.
- Stopping or replacing a running Herdr server without the user's OK.
- Approving a `herdr machine add` install or replace prompt.
- Deleting a known-hosts entry because a host key changed, without the user.
- Passing build parameters with `--parameter` when their names contain spaces.
- Passing `~` to Herdr `--cwd` options on a remote machine.
- Reporting a step as done without its verification.
