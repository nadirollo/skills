# Files written by setup

Placeholders: `<ws>` is the Coder workspace name, `<coder-user>` the Coder
username (`coder whoami`), `<coder-url>` the workspace's `CODER_URL`
(`ssh <ws> printenv CODER_URL`). Write each file only if it is missing or
differs; back up a differing file as `<file>.bak-<YYYYMMDD>` first.

## Laptop

### `~/.ssh/conf.d/<ws>`

```sshconfig
Host <ws>
    HostName <ws>
    User <coder-user>
    ProxyCommand <absolute-path-to-coder> ssh --stdio --disable-autostart <ws>
    HostKeyAlias <ws>-coder
    UserKnownHostsFile ~/.ssh/known_hosts.<ws>-coder
    StrictHostKeyChecking yes
    ControlPath ~/.ssh/control/<ws>-coder-%C
```

Mode `600`. `~/.ssh/config` must contain `Include conf.d/*` **before** any
`Host *` block: SSH uses the first value it finds, so a `User` under `Host *`
earlier in the file would override `<coder-user>`. Create
`~/.ssh/control/` (mode `700`) if missing.

`--disable-autostart` keeps Herdr's reconnect attempts from starting a
stopped workspace.

## Workspace

### Shell setup

Append to `~/.bashrc` if absent:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Append to `~/.profile` if absent, so `systemctl --user` works over SSH:

```bash
if [ -d "/run/user/$(id -u)" ]; then
    export XDG_RUNTIME_DIR="/run/user/$(id -u)"
    export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
fi
```

### `~/.local/bin/with-coder-github` (mode `700`)

Gets a fresh GitHub token from Coder external auth for each command. Tokens
expire, so a token exported once at shell start goes stale in long-lived
Herdr panes.

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

```bash
#!/usr/bin/env bash
set -euo pipefail
exec "$HOME/.local/bin/with-coder-github" "$HOME/.local/opt/copilot/copilot" "$@"
```

### `~/.config/environment.d/git.conf`

Gives processes started by the systemd user manager (the Herdr server and
every pane) the same Git identity as Coder sessions. Copy the values from the
workspace session environment (`printenv | grep '^GIT_'`):

```ini
GIT_AUTHOR_EMAIL="<value>"
GIT_AUTHOR_NAME="<value>"
GIT_COMMITTER_EMAIL="<value>"
GIT_COMMITTER_NAME="<value>"
```

### `~/.config/systemd/user/herdr.service`

```ini
[Unit]
Description=Persistent Herdr agent workspace
StartLimitIntervalSec=0

[Service]
Type=simple
WorkingDirectory=%h/workspace
Environment=PATH=%h/.local/bin:/usr/local/bin:/usr/bin:/bin:/snap/bin
Environment=CODER_AGENT_AUTH=google-instance-identity
Environment=CODER_AGENT_URL=<coder-url>
Environment=CODER_URL=<coder-url>
Environment=SHELL=/bin/bash
Environment=TERM=xterm-256color
UMask=0077
ExecStart=%h/.local/bin/herdr server
Restart=always
RestartSec=5
TimeoutStopSec=30
KillMode=control-group

[Install]
WantedBy=default.target
```

Create `~/workspace` first. Then:

```bash
sudo loginctl enable-linger "$USER"   # keep user services running without a login
systemctl --user daemon-reload
systemctl --user enable --now herdr.service
```

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
