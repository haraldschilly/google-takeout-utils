# google-takeout-utils

CLI tools for searching, reading, and extracting data from Google Takeout exports.
Designed to work with the mbox email export — no conversion or import into an email client needed.

## Install

```bash
pip install google-takeout-utils
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install google-takeout-utils
```

This provides the `search-email` command.

## Setup

1. Extract your Google Takeout `.tgz` archives into a folder
2. Run `search-email` from within that folder, or use `--mbox` to point to the mbox file

```
your-takeout-folder/
├── Takeout/              ← extracted Google Takeout data
│   └── Mail/
│       └── All mail Including Spam and Trash.mbox
├── utils/                ← this repo (clone here)
└── search-email.sh       ← wrapper script
```

Requires [uv](https://docs.astral.sh/uv/) and Python 3.10+.

### Wrapper script

Create `search-email.sh` next to `Takeout/` and `utils/`:

```bash
#!/bin/bash
ORIG_DIR="$(pwd)"
cd "$(dirname "$0")/utils"
exec uv run search_email.py --output-dir "$ORIG_DIR" "$@"
```

```bash
chmod +x search-email.sh
```

The wrapper ensures `uv` resolves dependencies from the `utils/` project,
while `--output-dir` defaults to your current working directory for attachment extraction.

## How it works

On first run, the tool scans the entire mbox file and builds a **SQLite index**
(`Takeout/Mail/index.sqlite`) containing date, sender, subject, and attachment flags
for every email. This takes ~2 minutes for a typical 8GB inbox.

After indexing, all searches query the SQLite database and return results instantly.
Body text and attachments are fetched on demand by seeking to the byte offset in the mbox file.

The index is **not** included in version control (`.gitignore`). It is rebuilt automatically
when missing, e.g. after a fresh Google Takeout import.

## Usage

### Search emails

```bash
# Search by sender (case-insensitive substring match on name or email)
./search-email.sh --from alice

# Date range + sender, limit results
./search-email.sh --date-from 2023-01-01 --date-to 2023-07-01 --from john --limit 20

# Search by subject
./search-email.sh --subject "invoice" --limit 5

# Only emails with attachments
./search-email.sh --has-attachment --from bank --no-body

# Count matches
./search-email.sh --count --from newsletter

# Full-text body search (slower — seeks into mbox for each candidate)
./search-email.sh --body "project proposal" --limit 5

# Headers only, no body preview
./search-email.sh --from alice --no-body
```

Search results are sorted by date (newest first). Each result shows a database ID
and an `[A]` marker if the email has attachments.

### Read a single email

```bash
# Show full email by database ID (from search results)
./search-email.sh --show 4521

# As JSON (useful for piping to other tools or LLMs)
./search-email.sh --show 4521 --output json

# As YAML
./search-email.sh --show 4521 --output yaml
```

`--show` displays the complete body and lists all attachments with their extract commands.

### Extract attachments

```bash
# Save first attachment of email 4521 to current directory
./search-email.sh --attachment 4521-1

# Save to a specific directory
./search-email.sh --attachment 4521-2 --output-dir /tmp
```

Use `--show ID` first to see available attachments and their index numbers.

### Index management

```bash
# Force rebuild (e.g. after a new Google Takeout export)
./search-email.sh --re-index
```

## Options reference

### Search filters

| Option | Description |
|--------|-------------|
| `--from TEXT` | Case-insensitive substring match on From header (name or email) |
| `--subject TEXT` | Case-insensitive substring match on Subject |
| `--body TEXT` | Case-insensitive substring match in body text (slower) |
| `--date-from YYYY-MM-DD` | Emails on or after this date (UTC, inclusive) |
| `--date-to YYYY-MM-DD` | Emails before this date (UTC, exclusive) |
| `--has-attachment` | Only emails with file attachments |
| `--limit N` | Max results (default: 10) |
| `--count` | Only print match count |

### Display

| Option | Description |
|--------|-------------|
| `--no-body` | Omit body preview in search results |
| `--output text\|json\|yaml` | Output format (default: text) |

### Actions

| Option | Description |
|--------|-------------|
| `--show ID` | Show full email by database ID |
| `--attachment ID-N` | Extract attachment N from email ID (e.g. `4521-1`) |
| `--output-dir PATH` | Directory for extracted attachments (default: cwd) |

### Index

| Option | Description |
|--------|-------------|
| `--re-index` | Force rebuild the SQLite index |
| `--mbox PATH` | Path to mbox file (auto-detected by default) |

## License

Apache 2.0 — see [LICENSE](LICENSE).
