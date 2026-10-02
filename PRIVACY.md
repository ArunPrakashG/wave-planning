# Privacy Policy

**wave-planning** (the "plugin") · Last updated: 2026-10-02

This plugin runs locally inside Claude Code. This policy describes what the plugin itself does with data. It does not replace Anthropic's own terms and privacy policy, which govern how Claude Code and Claude process what you send them.

## What the plugin collects

Nothing. The plugin has no analytics, no telemetry, no accounts, and no server. The author does not receive any information about you, your projects, or your use of the plugin.

## What the plugin reads and writes

- It reads and writes files **in your own project**: `plan.md`, `docs/waves/specs/`, `docs/waves/design/`, and the source files your plan assigns to each phase.
- It creates local git branches and worktrees in your repository (`wave/integration`, `wave/<n>/<phase>`, `.worktrees/`). It does not push to any remote unless you explicitly agree to it.
- It runs the format, lint, type-check, test and bootstrap commands that you confirmed in your plan.
- It stores nothing outside your project directory.

## Network access

- The plugin's bundled scripts (`validate_plan.py`, `routing.py`, `check_owned.py`, `http_check.py`) do not contact any external service. `http_check.py` only makes requests to loopback addresses (`localhost`, `127.0.0.1`, `::1`) on your own machine, to check an app you are running locally, unless you deliberately pass `--allow-remote`.
- The plugin does not read your credentials, tokens, or API keys.

## Data that goes to Anthropic

When you use Claude Code, the content that Claude and its subagents read and write, including your plan, specs, design and code, is processed by Anthropic under your own Claude plan and Anthropic's terms. The plugin does not add any other recipient. If you ask the `wave-design` skill to build a mockup in Claude Design, that mockup is created under your own Claude account and is governed by Anthropic's terms for that product.

## Third parties

The plugin does not share data with any third party.

## Contact and changes

Questions or concerns: open an issue at https://github.com/ArunPrakashG/wave-planning/issues. Changes to this policy are made in this repository and the date above is updated.
