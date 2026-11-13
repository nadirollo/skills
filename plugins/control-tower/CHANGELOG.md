<!-- markdownlint-disable MD024 -->

# Changelog

All notable changes to the `control-tower` plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [0.3.0] - 2026-11-13

### Changed

- **Breaking:** `dispatch` now drives herdr-core (`hc`) and herdr-app instead
  of the `herdr` terminal app. One task runs in one herdr-app space with its
  own tower. Workers start with `hc run --bg --outlive-parent` and their
  prompt in the same command, carry `herdr.space`, `ct.task`, `ct.role` and
  `ct.worker` labels, and appear as tabs in the task's space.
- Watching uses a background `hc wait --children any`; workers report with
  `hc send <tower>`. Escalation no longer shows a Herdr notification: the
  tower ends its turn and herdr-app's agents list shows it waiting.
- Coding workers get plain `git worktree` checkouts under
  `~/.herdr/worktrees/<repo>/<branch>`; cleanup kills and removes the task's
  terminals and worktrees and leaves closing the space to the user.
- The worker prompt forbids starting other agents.
- The tower relays worker prompts: it reads a blocked worker's dialog, asks
  the user in its own chat (up to four workers per question), types only the
  user's answer with `hc keys` or `hc send --force`, and checks the dialog
  closed. The user never has to switch to a worker tab.

### Added

- Per-task delegated approvals: classes of worker prompts the user hands to
  the tower, recorded in `log.md` and answered without asking. Merges,
  releases, deploys, infrastructure applies, secrets, shared-system uploads
  and dev/production access are never delegable.

### Migration

- Start the tower inside a herdr-app space on the machine where workers run
  (one space per task) instead of a Herdr pane.
- Tasks started with 0.2.0 keep their `herdr` workers; finish or clean them
  up with the `herdr` CLI.
- `setup` is not ported yet: it still installs the `herdr` terminal app.

## [0.2.0] - 2026-11-11

### Added

- `setup` skill: sets up, checks and repairs an always-on Coder workspace
  for Herdr and control-tower from the laptop. Creates or reuses a
  `gcp-dev-generic` workspace, installs Herdr as a systemd user service with
  the Radar and Bar plugins, Claude Code, Coder-backed GitHub auth and
  optional tools, mirrors non-secret model settings, and saves the workspace
  as a Herdr machine.

## [0.1.0] - 2026-11-11

### Added

- `dispatch` skill: optional grilling interview, approved specs, worker
  launch in Herdr workspaces or worktrees, background watching, reports,
  follow-ups, escalation and cleanup.
- Bundled copy of Matt Pocock's `grilling` instructions (MIT).
