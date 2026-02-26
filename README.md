# google-takeout-utils

CLI tools for searching, reading, and extracting emails from Google Takeout mbox exports.
No conversion or import into an email client needed.

## Quick start

No install needed — run directly from PyPI with [uvx](https://docs.astral.sh/uv/):

```bash
cd /path/to/your/takeout-folder
uvx google-takeout-utils@latest search-email --help
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

All examples use `uvx`. If installed globally, replace `uvx google-takeout-utils@latest` with just `google-takeout-utils`.

### Search emails

```bash
# Search by sender (case-insensitive substring match on name or email)
uvx google-takeout-utils@latest search-email --from alice

# Date range + sender, limit results
uvx google-takeout-utils@latest search-email --after 2023-01-01 --before 2023-07-01 --from john --limit 20

# Search by recipient (searches To, CC, and BCC)
uvx google-takeout-utils@latest search-email --to alice@example.com

# Search by subject
uvx google-takeout-utils@latest search-email --subject "invoice" --limit 5

# Only emails with attachments
uvx google-takeout-utils@latest search-email --has-attachment --from bank --no-body

# Count matches
uvx google-takeout-utils@latest search-email --count --from newsletter

# Full-text body search (slower — seeks into mbox for each candidate)
uvx google-takeout-utils@latest search-email --body "project proposal" --limit 5

# Headers only, no body preview
uvx google-takeout-utils@latest search-email --from alice --no-body
```

Search results are sorted by date (newest first). Each result shows a database ID
and an `[A]` marker if the email has attachments.

### Read a single email

```bash
# Show full email by database ID (from search results)
uvx google-takeout-utils@latest search-email --show 4521

# As JSON (useful for piping to other tools or LLMs)
uvx google-takeout-utils@latest search-email --show 4521 --output json

# As YAML
uvx google-takeout-utils@latest search-email --show 4521 --output yaml
```

`--show` displays the complete body, To/CC/BCC recipients, and lists all attachments with their extract commands.

### View email threads

```bash
# Reconstruct the full thread containing email 4521
uvx google-takeout-utils@latest search-email --thread 4521
```

Shows an indented tree of all related emails with their database IDs, subjects (truncated to 70 chars), senders, and dates. The starting email is marked with `<--`.

### Extract attachments

```bash
# Save first attachment of email 4521 to current directory
uvx google-takeout-utils@latest search-email --attachment 4521-1

# Save to a specific directory
uvx google-takeout-utils@latest search-email --attachment 4521-2 --output-dir /tmp
```

Use `--show ID` first to see available attachments and their index numbers.

### Index management

```bash
# Force rebuild (e.g. after a new Google Takeout export)
uvx google-takeout-utils@latest search-email --re-index
```

## How it works

On first run, the tool scans the entire mbox file and builds a **SQLite index**
(`Takeout/Mail/index.sqlite`) containing date, sender, recipients (To/CC/BCC), subject,
attachment flags, and threading information (Message-ID, In-Reply-To) for every email.
Threads are precomputed using Union-Find on In-Reply-To chains.

After indexing, all searches query the SQLite database and return results instantly.
Body text and attachments are fetched on demand by seeking to the byte offset in the mbox file.

The index is rebuilt automatically when missing (e.g. after a fresh Takeout import).

## Options reference

### Search filters

| Option | Description |
|--------|-------------|
| `--from TEXT` | Case-insensitive substring match on From header (name or email) |
| `--to TEXT` | Case-insensitive substring match on To/CC/BCC headers |
| `--subject TEXT` | Case-insensitive substring match on Subject |
| `--body TEXT` | Case-insensitive substring match in body text (slower) |
| `--after YYYY-MM-DD` | Emails on or after this date (UTC, inclusive) |
| `--before YYYY-MM-DD` | Emails before this date (UTC, exclusive) |
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
| `--thread ID` | Show full email thread as indented tree |
| `--attachment ID-N` | Extract attachment N from email ID (e.g. `4521-1`) |
| `--output-dir PATH` | Directory for extracted attachments (default: cwd) |

### Index

| Option | Description |
|--------|-------------|
| `--re-index` | Force rebuild the SQLite index |
| `--mbox PATH` | Path to mbox file (auto-detected by default) |

## License

Apache 2.0 — see [LICENSE](LICENSE).
