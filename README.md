# nadirollo/skills

Personal staging area for agent skills I want to test myself before
contributing widely.

## Location

## Adding a skill

1. Create `plugins/<plugin>/.claude-plugin/plugin.json` and
   `plugins/<plugin>/skills/<skill>/SKILL.md`.
2. Add the plugin to `.claude-plugin/marketplace.json` with
   `"source": "./plugins/<plugin>"`.
3. Validate: `claude plugin validate .`

## Testing locally

```
claude plugin marketplace add ~/workspace/ai-hub/skills   # laptop
claude plugin marketplace add ~/workspace/skills          # ai-hub
claude plugin install <plugin>@nadirollo-skills --scope user
```

After editing a skill, run `claude plugin marketplace update nadirollo-skills`
and `claude plugin update <plugin>@nadirollo-skills --scope user`, then start a
new session.
