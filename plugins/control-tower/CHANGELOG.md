<!-- markdownlint-disable MD024 -->

# Changelog

All notable changes to the `control-tower` plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [0.3.0] - 2026-11-13

### Added

- `dispatch` skill: runs a Claude session as the control tower for one task,
  in its own herdr-app space.
  - Optional grilling interview (bundled copy of Matt Pocock's `grilling`
    instructions, MIT), then a spec per worker.
  - Spec review in Lavish: each spec is rendered to `spec.html` from
    `references/spec-review.html` and opened over Coder Connect; the user
    annotates it and approves a numbered revision. Review in the chat is the
    fallback.
  - Workers start with `hc run --bg --outlive-parent`, their prompt in the
    same command, in a git worktree or the repo, and appear as tabs in the
    task's space through the `herdr.space` label. Fixed worker rules: draft
    PRs at most, never merge or release, no sub-agents.
  - Watching with a background `hc wait --children any`; workers report with
    `hc send`. Follow-ups for review, CI and PR comments.
  - The tower relays every worker prompt to the user in its own chat and
    types only the user's answer; per-task delegated approvals for routine
    prompts, with merges, releases, deploys, infrastructure applies, secrets,
    shared-system uploads and dev/production access never delegable.
  - Cleanup of the task's terminals, worktrees and Lavish sessions; the task
    folder is kept.
- `setup` skill: from the laptop, sets up, checks and repairs everything the
  tower needs.
  - Coder: a `gcp-dev-generic` workspace with no auto-stop, and an SSH alias
    with strict host-key checking.
  - Workspace: herdr-core with linger, Claude Code, Node, Coder-backed GitHub
    auth, mirrored model settings, Lavish pinned at 0.1.96 with
    `~/.config/control-tower/lavish.env`, optional tools, and optional
    Claude Code preferences (status line, 365-day history).
  - Laptop: herdr-app with the workspace as a machine, and Coder Desktop with
    Coder Connect, verified end to end against Lavish.
