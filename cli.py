#!/usr/bin/env python3
"""google-takeout-utils: CLI tools for working with Google Takeout exports.

Usage:
    google-takeout-utils search-email [OPTIONS]
    google-takeout-utils <command> [OPTIONS]

Available commands:
    search-email    Search, read, and extract emails from the mbox export
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        prog="google-takeout-utils",
        description="CLI tools for working with Google Takeout exports.",
        epilog="""
AVAILABLE COMMANDS:
  search-email   Search, read, and extract emails from the Gmail mbox export.
                 Builds a SQLite index for instant lookups. Supports filtering
                 by date, sender, subject, body, and attachments.
                 Run 'google-takeout-utils search-email --help' for details.

QUICK START:
  cd /path/to/your/extracted/takeout
  uvx google-takeout-utils@latest search-email --from alice --limit 5

  Or point to the takeout directory from anywhere:
  uvx google-takeout-utils@latest --takeout-dir /path/to/takeout search-email --from alice
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--takeout-dir", type=str, default=None,
        help="Path to the root directory containing the Takeout/ folder "
             "(e.g. the extracted Google Takeout zip). "
             "If not set, the tool looks relative to the current working directory.",
    )

    subparsers = parser.add_subparsers(dest="command", title="commands")

    # --- search-email ---
    from search_email import register_subcommand as register_search_email
    register_search_email(subparsers)

    # future: register_drive(subparsers), etc.

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
