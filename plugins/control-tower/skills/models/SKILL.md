---
name: models
description: Use when the user invokes /control-tower:models, or when dispatch or setup needs the list of models each installed agent harness (Claude Code, Copilot CLI) offers on this machine. Starts each harness in a hidden hc session, reads its model list from the harness itself, and writes ~/.config/control-tower/models.json, which the dispatch spec approval page loads into its model and effort dropdowns. Costs nothing: no prompt reaches a model.
argument-hint: "[harness,...]"
---

# Models

Refresh the models each installed harness offers, for the dispatch spec
approval page. Run it on the machine where workers run (the Coder
workspace), not on the laptop.

Harnesses to refresh (empty: all installed): $ARGUMENTS

## What it writes

`~/.config/control-tower/models.json`:

```json
{
  "generated_at": "2026-11-13T23:40:00+00:00",
  "machine": "ai-hub",
  "harnesses": [
    { "id": "claude", "label": "Claude Code", "version": "2.1.325 (Claude Code)",
      "probed_at": "...",
      "models": [
        { "id": "default", "label": "default (harness setting: Opus 5.5)" },
        { "id": "opus", "label": "Opus 5.5 · us.anthropic.claude-opus-5-5[1m]",
          "model": "us.anthropic.claude-opus-5-5[1m]" }
      ],
      "efforts": ["default", "low", "medium", "high", "xhigh", "max"] },
    { "id": "copilot", "label": "Copilot CLI", "version": "...", "probed_at": "...",
      "models": [
        { "id": "default", "label": "default (Copilot setting)" },
        { "id": "auto", "label": "auto (Copilot picks)" },
        { "id": "gpt-6.1-sol", "label": "GPT-6.1 Sol", "group": "Recommended models",
          "default_effort": "medium" },
        { "id": "claude-haiku-4.5", "label": "Claude Haiku 4.5", "group": "Other models",
          "efforts": ["default"] }
      ],
      "efforts": ["default", "none", "minimal", "low", "medium", "high", "xhigh", "max"],
      "unavailable": ["grok-4.7"] }
  ]
}
```

- `id` is what the worker is launched with (`--model <id>`); `default`
  passes no flag. A model's own `efforts` (when present) narrows the
  harness's list: `["default"]` means it takes no effort setting.
- Only installed harnesses appear. A harness whose probe failed keeps its
  previous entry with `"stale": true`.

## Run it

```bash
export PATH="$HOME/.local/bin:$PATH"
script="${CLAUDE_SKILL_DIR}/scripts/probe_models.py"
[ -f "$script" ] || script=$(ls -d ~/.claude/plugins/cache/*/control-tower/*/skills/models/scripts/probe_models.py 2>/dev/null | sort -V | tail -1)
python3 -I "$script"            # with arguments: --only <harness,...>
```

Run it in the foreground: it takes about a minute.

How it reads each harness:

| Harness | How |
| --- | --- |
| `claude` | Opens the `/model` picker: its aliases (`default`, `sonnet`, `fable`, `opus`, `haiku`) and the model each points at. Efforts from `claude --help`. |
| `copilot` | `/model ct-list-models` makes Copilot print every model ID it accepts; the `/model` picker adds display names, groups, default efforts, and which models are unavailable (left out). Efforts from `copilot --help`. |

The sessions run in hidden hc terminals (no parent, no `herdr.space`
label), in `~/.cache/control-tower/model-probe`, and are removed at the end.
If a harness asks to trust that empty folder, the script says yes for it
only (Copilot: this session only).

## Report

Tell the user, per harness: how many models, the version, and whether it
failed (with the error). Exit status 1 means at least one harness failed;
say which, and that the page keeps its previous list for it. Do not edit
the file by hand.

## When to run it

- `/control-tower:setup` runs it once on the workspace.
- Again after a harness update, or when the user says a model is missing.
- dispatch notes when the file is older than 7 days, or missing, and offers
  to run it; it never blocks a spec approval on it.

## Adding a harness

Add a `probe_<id>` function to `scripts/probe_models.py` that starts the
harness interactively, reads its model list from the harness itself, and
returns the same shape; register it in `PROBES`. Add the harness to
`dispatch/references/harnesses.md` too.
