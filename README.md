# google-takeout-utils

CLI utilities for working with Google Takeout exports.

## Setup

Clone this repo next to your extracted `Takeout` directory:

```
your-takeout-folder/
├── Takeout/          ← extracted Google Takeout data
├── utils/            ← this repo
└── search-email.sh   ← wrapper script (see below)
```

Requires [uv](https://docs.astral.sh/uv/) and Python 3.10+.

## search-email.sh

Create a wrapper script next to `Takeout/` and `utils/`:

```bash
#!/bin/bash
cd "$(dirname "$0")/utils"
exec uv run search_email.py "$@"
```

```bash
chmod +x search-email.sh
```

## Usage

On first run, the tool automatically builds a SQLite index of all email headers
(`Takeout/Mail/index.sqlite`). This takes ~2 minutes for a typical inbox and only
needs to happen once. Subsequent searches are instant.

```bash
# Search by sender
./search-email.sh --from someone@example.com

# Search by date range and sender
./search-email.sh --date-from 2023-01-01 --date-to 2023-02-01 --from john --limit 10

# Search by subject
./search-email.sh --subject "invoice" --limit 5

# Count matches without printing
./search-email.sh --count --from newsletter

# Search in body text (slower, seeks into mbox for each candidate)
./search-email.sh --body "project proposal" --limit 5

# Headers only, no body preview
./search-email.sh --from alice --no-body

# Rebuild the index (e.g. after a new Takeout export)
./search-email.sh --re-index
```

### Options

| Option | Description |
|--------|-------------|
| `--from TEXT` | Case-insensitive match on From header |
| `--subject TEXT` | Case-insensitive match on Subject |
| `--body TEXT` | Case-insensitive match in body text |
| `--date-from YYYY-MM-DD` | Start date (inclusive) |
| `--date-to YYYY-MM-DD` | End date (exclusive) |
| `--limit N` | Max results (default: 10) |
| `--no-body` | Don't show body preview |
| `--count` | Only count matches |
| `--re-index` | Force rebuild the SQLite index |
| `--mbox PATH` | Path to mbox file (auto-detected by default) |

## License

Apache 2.0 - see [LICENSE](LICENSE).
