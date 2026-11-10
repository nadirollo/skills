# nadirollo/skills

Personal staging area for agent skills I want to test myself before
contributing them to `fastly/agent-skills-internal`.

## Layout

Mirrors `fastly/agent-skills-internal`, so a plugin can be copied over as-is:

```
.claude-plugin/marketplace.json      # lists every plugin in this repo
plugins/<plugin>/.claude-plugin/plugin.json
plugins/<plugin>/skills/<skill>/SKILL.md
```

## Adding a skill

1. Create `plugins/<plugin>/.claude-plugin/plugin.json` and
   `plugins/<plugin>/skills/<skill>/SKILL.md`.
2. Add the plugin to `.claude-plugin/marketplace.json` with
   `"source": "./plugins/<plugin>"`.
3. Validate: `claude plugin validate .`

## Testing locally

```
claude plugin marketplace add ~/workspace/personal/skills
claude plugin install <plugin>@nadirollo-skills --scope user
```

After editing a skill, run `claude plugin marketplace update nadirollo-skills`
and `claude plugin update <plugin>@nadirollo-skills --scope user`, then start a
new session.

## Contributing to Fastly

Once a skill has proven itself, copy `plugins/<plugin>/` into
`fastly/agent-skills-internal`, follow that repo's `CONTRIBUTING.md`
(author, versioning, changelog, checks), and open a PR there.
