# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2026-02-26

### Added

- Top-level `--takeout-dir` option to point to the takeout root from anywhere
- `CLAUDE.md` and `AGENTS.md` project documentation

## [0.1.1] - 2026-02-25

### Fixed

- Stale command reference in README after subcommand restructure

## [0.1.0] - 2026-02-25

### Added

- Initial release
- SQLite-indexed search over Google Takeout mbox exports
- Search filters: `--from`, `--subject`, `--body`, `--date-from`, `--date-to`, `--has-attachment`
- Single-email view with `--show ID`
- Attachment extraction with `--attachment ID-N`
- Output formats: text, JSON, YAML
- Subcommand CLI structure (`google-takeout-utils search-email`)
- Auto-detect mbox from cwd for `uvx` usage
- PyPI publishing via GitHub Actions

[0.1.2]: https://github.com/haraldschilly/google-takeout-utils/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/haraldschilly/google-takeout-utils/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/haraldschilly/google-takeout-utils/releases/tag/v0.1.0
