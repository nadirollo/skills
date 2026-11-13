# Harnesses

The agent CLIs a worker can run in, with their model and effort options. The
spec review page offers these as dropdowns, and the launch command is built
from them. Offer only harnesses installed on the machine (`command -v <bin>`).

| Harness | Binary | Model flag | Models offered | Effort flag | Efforts offered | First prompt |
| --- | --- | --- | --- | --- | --- | --- |
| `claude` | `claude` | `--model <m>` | `fable`, `opus`, `sonnet`, `haiku` (aliases for the latest of each; full model IDs also work) | `--effort <e>` | `low`, `medium`, `high`, `xhigh`, `max` | last argument: `claude ... '<prompt>'` |
| `copilot` | `copilot` (the setup wrapper: GitHub auth through Coder, `--yolo`) | `--model <m>` | `auto` (Copilot picks) | `--reasoning-effort <e>` | `none`, `minimal`, `low`, `medium`, `high`, `xhigh`, `max` | `-i '<prompt>'` (interactive with a first prompt; never `-p`) |

Every harness also gets two entries that are not flags:

- **`default`** (model or effort): pass no flag, so the harness uses its own
  configuration (for Claude Code, `model` in `~/.claude/settings.json`).
- **Other…** (model only): the user types a model name. Use it only if it
  matches `^[A-Za-z0-9][A-Za-z0-9._:/@\[\]-]{0,99}$`; otherwise ask in the
  chat.

## Building the launch command

Use the values from the approval prompt (see dispatch step 3a), never from a
note. Before using them, check that the harness is in this table and
installed, the effort is one of its listed values or `default`, and the model
is listed, `default`, or a valid Other name. Single-quote the model in the
command.

```bash
# claude
hc run --bg --json --outlive-parent <hc options> \
  claude [--model '<model>'] [--effort <effort>] '<filled worker prompt>'

# copilot
hc run --bg --json --outlive-parent <hc options> \
  copilot [--model '<model>'] [--reasoning-effort <effort>] -i '<filled worker prompt>'
```

Leave out a flag whose value is `default`.

## The page's harness data

The spec review page reads this JSON (template slot `{{HARNESSES_JSON}}`).
Include only installed harnesses, in this table's order. `defaults` is what
the page preselects: the task's settings (dispatch Settings, or the user's
override in `log.md`).

```json
{
  "harnesses": [
    { "id": "claude", "label": "Claude Code",
      "models": ["default", "fable", "opus", "sonnet", "haiku"],
      "efforts": ["default", "low", "medium", "high", "xhigh", "max"] },
    { "id": "copilot", "label": "Copilot CLI",
      "models": ["default", "auto"],
      "efforts": ["default", "none", "minimal", "low", "medium", "high", "xhigh", "max"] }
  ],
  "defaults": {
    "worker": { "harness": "claude", "model": "default", "effort": "default" },
    "reviewer": { "harness": "claude", "model": "opus", "effort": "high" }
  }
}
```

## Adding a harness

To add one (for example Codex), read its `--help` and add a row: the binary,
how it takes a model and an effort, its accepted effort values, and how it
starts **interactively** with a first prompt (hc workers must stay
interactive, never a one-shot print mode). Then add its entry to the JSON
above. If it needs a wrapper for GitHub auth or to skip permission prompts,
add that to the `setup` skill too.
