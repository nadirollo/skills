# Files written by setup

Placeholders: `<ws>` is the Coder workspace name, `<coder-user>` the Coder
username (`coder whoami`), `<coder-url>` the workspace's `CODER_URL`
(`ssh <ws> printenv CODER_URL`). Write each file only if it is missing or
differs; back up a differing file as `<file>.bak-<YYYYMMDD>` first.

## Laptop

### `~/.ssh/conf.d/<ws>` (suggested to the user; setup never writes it)

Show this, filled in, only when `ssh <ws>` does not already reach the
workspace. The user writes it.

```sshconfig
Host <ws>
    HostName <ws>
    User <coder-user>
    ProxyCommand <absolute-path-to-coder> ssh --stdio --disable-autostart <ws>
    HostKeyAlias <ws>-coder
    UserKnownHostsFile ~/.ssh/known_hosts.<ws>-coder
    StrictHostKeyChecking yes
    ControlMaster auto
    ControlPath ~/.ssh/control/<ws>-coder-%C
    ControlPersist yes
```

Mode `600`. `~/.ssh/config` must contain `Include conf.d/*` **before** any
`Host *` block: SSH uses the first value it finds, so a `User` under `Host *`
earlier in the file would override `<coder-user>`. `~/.ssh/control/` (mode
`700`) must exist. `ControlMaster`/`ControlPersist` reuse one connection for
herdr-app and `ssh <ws>` commands; drop them if the user prefers.

Then the user records the host key once (the connection runs through the
Coder CLI, which already authenticates the workspace):

```bash
ssh -o StrictHostKeyChecking=accept-new <ws> true
chmod 600 ~/.ssh/known_hosts.<ws>-coder
```

herdr-app reaches the workspace through this Host: its machine connection is
plain `ssh <ws>`. `--disable-autostart` keeps its reconnect attempts from
starting a stopped workspace.

## Workspace

### Shell setup

Append to `~/.bashrc` if absent:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Append to `~/.profile` if absent, so `systemctl --user` and `loginctl` work
over SSH:

```bash
if [ -d "/run/user/$(id -u)" ]; then
    export XDG_RUNTIME_DIR="/run/user/$(id -u)"
    export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
fi
```

### `~/.local/bin/with-coder-github` (mode `700`)

Gets a fresh GitHub token from Coder external auth for each command. Tokens
expire, so a token exported once at shell start goes stale in long-lived
terminals.

```bash
#!/usr/bin/env bash
set -euo pipefail
export CODER_AGENT_AUTH=google-instance-identity
export CODER_AGENT_URL=<coder-url>
if ! token="$(timeout 30 "$HOME/.local/bin/coder" external-auth access-token github)"; then
    printf 'Cannot refresh GitHub authentication through Coder. Check the GitHub external-auth connection in the Coder dashboard.\n' >&2
    exit 1
fi
if [[ -z "$token" ]]; then
    printf 'Coder returned an empty GitHub credential.\n' >&2
    exit 1
fi
export GITHUB_TOKEN="$token"
unset token
exec "$@"
```

`~/.local/bin/coder` is the server's own CLI:
`curl -fsSL -o ~/.local/bin/coder <coder-url>/bin/coder-linux-amd64` (use
`coder-linux-arm64` on arm64), then `chmod +x`.

### `~/.local/bin/gh` (mode `700`)

```bash
#!/usr/bin/env bash
set -euo pipefail
exec "$HOME/.local/bin/with-coder-github" /usr/bin/gh "$@"
```

Then make git use it for GitHub:

```bash
git config --global credential.https://github.com.helper '!'"$HOME"'/.local/bin/gh auth git-credential'
```

### `~/.local/bin/copilot` (mode `700`, only if Copilot CLI is chosen)

Copilot CLI is the latest release, unpacked into `~/.local/opt/copilot`.
`--yolo` runs it without permission prompts, like Claude Code in
`bypassPermissions` (see below).

```bash
#!/usr/bin/env bash
set -euo pipefail
exec "$HOME/.local/bin/with-coder-github" "$HOME/.local/opt/copilot/copilot" --yolo "$@"
```

### `~/.config/environment.d/git.conf`

Gives processes started by the systemd user manager the same Git identity as
Coder sessions, in case the hc core is ever started outside an SSH session.
Copy the values from the workspace session environment
(`printenv | grep '^GIT_'`):

```ini
GIT_AUTHOR_EMAIL="<value>"
GIT_AUTHOR_NAME="<value>"
GIT_COMMITTER_EMAIL="<value>"
GIT_COMMITTER_NAME="<value>"
```

### herdr-core

Installed with its own installer, which puts `herdr-core` and the `hc` link
in `~/.local/bin`:

```bash
curl -fsSL https://releases.herdr.dev/core/install.sh | sh
```

No service file: the core starts itself (as transient systemd user units)
when herdr-app connects, and keeps running after logout once linger is on:

```bash
sudo loginctl enable-linger "$USER"
```

### Lavish

Pinned, with npm install scripts off. The version is the one this plugin is
tested with; raise it only after checking the new release.

```bash
LAVISH_AXI_TELEMETRY=0 npm install -g --ignore-scripts lavish-axi@0.1.96
ln -sf "$(npm prefix -g)/bin/lavish-axi" "$HOME/.local/bin/lavish-axi"
```

Never run it through `npx -y lavish-axi`, which fetches whatever is latest.

### `~/.config/control-tower/lavish.env` (mode `600`)

Read by `dispatch` before every `lavish-axi` command. `<connect-host>` is the
workspace's Coder Connect name, `<ws>.<suffix>`; the suffix is `coder` unless
the deployment changed it (check the name Coder Desktop shows).

```bash
LAVISH_AXI_TELEMETRY=0
LAVISH_AXI_HOST=127.0.0.1
LAVISH_AXI_PORT=4387
LAVISH_AXI_NO_OPEN=1
LAVISH_AXI_DISCONNECT_GRACE_MS=off
LAVISH_AXI_ALLOWED_HOSTS=<connect-host>
LAVISH_AXI_LINK_HOST=<connect-host>
```

The server listens only on loopback; Coder Connect still delivers the
laptop's requests to it. Do not use the Coder port-share URL
(`https://4387--…`): its login proxy blocks Lavish's annotation script, and
the only way around that, a public port, would expose an unauthenticated
server that can read local files.

### `~/.claude/statusline.sh` (only if the user wants the status line)

```bash
#!/usr/bin/env bash
# Claude Code status line: model | cost | context % | dir
exec python3 -I -c '
import sys, json, os

try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
if not isinstance(d, dict):
    sys.exit(0)

def get(o, *keys):
    for k in keys:
        if not isinstance(o, dict): return None
        o = o.get(k)
    return o

parts = []
m = get(d, "model", "display_name")
if m: parts.append(str(m))

c = get(d, "cost", "total_cost_usd")
if isinstance(c, (int, float)): parts.append("$%.2f" % c)

p = get(d, "context_window", "used_percentage")
if isinstance(p, (int, float)): parts.append("ctx %d%%" % round(p))

cwd = get(d, "workspace", "current_dir") or d.get("cwd")
if cwd: parts.append(os.path.basename(str(cwd).rstrip("/")) or "/")

print(" | ".join(parts))
'
```

Mode `755`, and in `~/.claude/settings.json`:

```json
"statusLine": { "type": "command", "command": "bash <home>/.claude/statusline.sh" }
```

## Agent permissions on the workspace

Merged into the workspace's `~/.claude/settings.json` with `jq`, keeping any
existing `permissions.allow`, `permissions.deny` and other keys:

```json
{
  "permissions": { "defaultMode": "bypassPermissions" },
  "skipDangerousModePermissionPrompt": true
}
```

For example:

```bash
f=~/.claude/settings.json; [ -f "$f" ] || echo '{}' > "$f"
jq '.permissions.defaultMode = "bypassPermissions" | .skipDangerousModePermissionPrompt = true' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
```

Workspace only: never set these on the laptop.

## Model settings copied to the workspace

From the laptop's `~/.claude/settings.json`, copy **only** these keys if set,
merging them into the workspace's `~/.claude/settings.json` with `jq`:

| Key | Notes |
| --- | --- |
| `env.CLAUDE_CODE_USE_BEDROCK`, `env.CLAUDE_CODE_USE_VERTEX` | Provider switch. |
| `env.AWS_PROFILE`, `env.AWS_REGION` | Bedrock profile and region. |
| `env.ANTHROPIC_MODEL`, `env.ANTHROPIC_DEFAULT_OPUS_MODEL`, `env.ANTHROPIC_DEFAULT_SONNET_MODEL`, `env.ANTHROPIC_DEFAULT_HAIKU_MODEL` | Model IDs. |
| `env.CLOUD_ML_REGION`, `env.ANTHROPIC_VERTEX_PROJECT_ID` | Vertex. |
| `model` | Default model alias. |
| `awsAuthRefresh` | Rewrite to use `--use-device-code --no-browser`: the workspace has no browser. |

Never copy `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `apiKeyHelper`,
`awsCredentialExport`, any key containing `TOKEN`, `SECRET` or `KEY` (other
than the ones listed), `~/.claude/.credentials.json`, or `~/.claude.json`.

For Bedrock, copy from the laptop's `~/.aws/config` only the
`[profile <AWS_PROFILE>]` block and the `[sso-session <name>]` block it
references. Never copy `~/.aws/credentials`, `~/.aws/sso/cache/` or
`~/.aws/cli/cache/`.
