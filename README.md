# google-takeout-utils

CLI tools for searching, reading, and extracting emails from Google Takeout mbox exports.
No conversion or import into an email client needed.

## Quick start

No install needed — run directly from PyPI with [uvx](https://docs.astral.sh/uv/):

```bash
cd /path/to/your/takeout-folder
uvx --from google-takeout-utils@latest search-email --help
```

The `@latest` suffix ensures uvx always fetches the most recent version from PyPI.

## Setup

1. Download your data via [Google Takeout](https://takeout.google.com/)
2. Extract the `.tgz` archives into a folder
3. `cd` into that folder — the tool expects this layout:

```
your-takeout-folder/
└── Takeout/
    └── Mail/
        └── All mail Including Spam and Trash.mbox
```

On first run, a SQLite index is built automatically (~2 min for 8GB).
After that, all searches are instant.

## Install (optional)

For repeated use, install permanently so `search-email` is always available:

```bash
pip install google-takeout-utils
# or
uv tool install google-takeout-utils
```

## Usage

All examples use `uvx`. If installed, replace `uvx --from google-takeout-utils@latest` with just `search-email`.

### Search emails

```bash
# Search by sender (case-insensitive substring match on name or email)
uvx --from google-takeout-utils@latest search-email --from alice

# Date range + sender, limit results
uvx --from google-takeout-utils@latest search-email --date-from 2023-01-01 --date-to 2023-07-01 --from john --limit 20

# Search by subject
uvx --from google-takeout-utils@latest search-email --subject "invoice" --limit 5

# Only emails with attachments
uvx --from google-takeout-utils@latest search-email --has-attachment --from bank --no-body

# Count matches
uvx --from google-takeout-utils@latest search-email --count --from newsletter

# Full-text body search (slower — seeks into mbox for each candidate)
uvx --from google-takeout-utils@latest search-email --body "project proposal" --limit 5

# Headers only, no body preview
uvx --from google-takeout-utils@latest search-email --from alice --no-body
```

Search results are sorted by date (newest first). Each result shows a database ID
and an `[A]` marker if the email has attachments.

### Read a single email

```bash
# Show full email by database ID (from search results)
uvx --from google-takeout-utils@latest search-email --show 4521

# As JSON (useful for piping to other tools or LLMs)
uvx --from google-takeout-utils@latest search-email --show 4521 --output json

# As YAML
uvx --from google-takeout-utils@latest search-email --show 4521 --output yaml
```

`--show` displays the complete body and lists all attachments with their extract commands.

### Extract attachments

```bash
# Save first attachment of email 4521 to current directory
uvx --from google-takeout-utils@latest search-email --attachment 4521-1

# Save to a specific directory
uvx --from google-takeout-utils@latest search-email --attachment 4521-2 --output-dir /tmp
```

Use `--show ID` first to see available attachments and their index numbers.

### Index management

```bash
# Force rebuild (e.g. after a new Google Takeout export)
uvx --from google-takeout-utils@latest search-email --re-index
```

## How it works

On first run, the tool scans the entire mbox file and builds a **SQLite index**
(`Takeout/Mail/index.sqlite`) containing date, sender, subject, and attachment flags
for every email.

After indexing, all searches query the SQLite database and return results instantly.
Body text and attachments are fetched on demand by seeking to the byte offset in the mbox file.

The index is rebuilt automatically when missing (e.g. after a fresh Takeout import).

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
