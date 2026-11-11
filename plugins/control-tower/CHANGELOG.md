<!-- markdownlint-disable MD024 -->

# Changelog

All notable changes to the `control-tower` plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

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
