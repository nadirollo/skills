# Harnesses

The agent CLIs a worker can run in, with their model and effort options. The
spec review page offers these as dropdowns, and the launch command is built
from them. Offer only harnesses installed on the machine (`command -v <bin>`).

The models and efforts each harness offers come from
`~/.config/control-tower/models.json`, written by `/control-tower:models`
(and by setup), which asks each harness itself. The lists in the table below
are only the fallback when that file is missing or has no entry for a
harness.

| Harness | Binary | Model flag | Models offered | Effort flag | Efforts offered | First prompt |
| --- | --- | --- | --- | --- | --- | --- |
| `claude` | `claude` | `--model <m>` | fallback: `fable`, `opus`, `sonnet`, `haiku` (aliases for the latest of each; full model IDs also work) | `--effort <e>` | `low`, `medium`, `high`, `xhigh`, `max` | last argument: `claude ... '<prompt>'` |
| `copilot` | `copilot` (the setup wrapper: GitHub auth through Coder, `--yolo`) | `--model <m>` | fallback: `auto` (Copilot picks) | `--reasoning-effort <e>` | `none`, `minimal`, `low`, `medium`, `high`, `xhigh`, `max` | `-i '<prompt>'` (interactive with a first prompt; never `-p`) |

Every harness also gets two entries that are not flags:

- **`default`** (model or effort): pass no flag, so the harness uses its own
  configuration (for Claude Code, `model` in `~/.claude/settings.json`).
- **Other…** (model only): the user types a model name. Use it only if it
  matches `^[A-Za-z0-9][A-Za-z0-9._:/@\[\]-]{0,99}$`; otherwise ask in the
  chat.

## Building the launch command

Use the values from the approval prompt (see dispatch step 3a), never from a
note. Before using them, check that the harness is in this table and
installed; the model is one of its `models.json` ids (or the fallback list),
`default`, or a valid Other name; and the effort is in that model's
`efforts` if it has them, else the harness's. Single-quote the model in the
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

The spec review page reads one JSON object (template slot
`{{HARNESSES_JSON}}`): `harnesses` and `defaults`.

1. **`harnesses`:** from `~/.config/control-tower/models.json`, each entry's
   `id`, `label`, `models` and `efforts`, for installed harnesses only, in
   this table's order. A model is `{id, label, group?, efforts?}`; the page
   groups models by `group` and narrows the efforts to a model's own
   `efforts`. Copy them as they are.
2. If the file is missing, or has no entry for an installed harness, use the
   fallback lists from the table for it, as plain strings with `default`
   first. Tell the user once, in the chat, and offer to run
   `/control-tower:models` (about a minute); do not wait for it to show the
   spec.
3. If `generated_at` is older than 7 days, or an entry has `"stale": true`,
   use it anyway and mention it once.
4. **`defaults`:** what the page preselects, from the task's settings
   (dispatch Settings, or the user's override in `log.md`). A default model
   the list does not have shows as Other.

```json
{
  "harnesses": [
    { "id": "claude", "label": "Claude Code",
      "models": [{ "id": "default", "label": "default (harness setting: Opus 5.5)" },
                 { "id": "opus", "label": "Opus 5.5 · us.anthropic.claude-opus-5-5[1m]" }],
      "efforts": ["default", "low", "medium", "high", "xhigh", "max"] },
    { "id": "copilot", "label": "Copilot CLI",
      "models": [{ "id": "default", "label": "default (Copilot setting)" },
                 { "id": "gpt-6.1-sol", "label": "GPT-6.1 Sol", "group": "Recommended models" },
                 { "id": "claude-haiku-4.5", "label": "Claude Haiku 4.5", "group": "Other models", "efforts": ["default"] }],
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
interactive, never a one-shot print mode). Add a probe for it to the
`models` skill's script, so its models are read from the harness itself. If
it needs a wrapper for GitHub auth, to skip permission prompts, or to trust
folders, add that to the `setup` skill too.
