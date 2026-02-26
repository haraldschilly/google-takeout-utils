# CLAUDE.md

## Project Overview

`google-takeout-utils` is a zero-dependency Python CLI for searching, reading, and extracting emails from Google Takeout mbox exports. It uses a SQLite index for fast lookups.

## Development Reminders

- **Do not leak private or sensitive information.** This tool processes personal email data. Never log, print, or expose email content, sender addresses, or other PII in error messages, debug output, or committed test fixtures.
- **Always use `uv`** for running Python, e.g. `uv run python3 ...` to stay in the uv environment.
- **Release checklist:** When tagging a new version, after pushing the tag, add a corresponding entry to `CHANGELOG.md` (follows [Keep a Changelog](https://keepachangelog.com/) format) and push it as a follow-up commit.

## Project Structure

- `cli.py` — Main entry point, top-level argument parser with subcommands
- `search_email.py` — Core search-email subcommand (indexing, searching, extraction)
- `pyproject.toml` — Package config (hatchling build, zero runtime dependencies)

## Key Commands

```bash
# Run from project directory
uv run python3 cli.py search-email --from alice --limit 5

# With takeout dir (works from anywhere)
uv run python3 cli.py --takeout-dir /path/to/takeout search-email --from alice

# Via uvx
uvx google-takeout-utils@latest --takeout-dir /path/to/takeout search-email --from alice
```

## Architecture Notes

- **No external dependencies** — uses only Python stdlib
- **Subcommand pattern** — `cli.py` dispatches to subcommand modules via `register_subcommand()`
- **Top-level `--takeout-dir`** applies to all subcommands; `--mbox` is search-email-specific
- **Lazy body reads** — index stores byte offsets, body text only read on demand
- Entry point: `google-takeout-utils = "cli:main"` in pyproject.toml
