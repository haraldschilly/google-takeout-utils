#!/usr/bin/env python3
"""Search through Google Takeout mbox email export.

Uses a SQLite index for fast lookups. On first run (or with --re-index),
scans the mbox file and builds an index at ./Takeout/Mail/index.sqlite.
Subsequent searches query the index and only seek into the mbox for body text.
"""

import argparse
import email
import email.utils
import email.header
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

MBOX_PATH = Path(__file__).parent.parent / "Takeout" / "Mail" / "All mail Including Spam and Trash.mbox"
INDEX_PATH = Path(__file__).parent.parent / "Takeout" / "Mail" / "index.sqlite"


def decode_header(raw):
    if raw is None:
        return ""
    parts = email.header.decode_header(raw)
    decoded = []
    for data, charset in parts:
        if isinstance(data, bytes):
            decoded.append(data.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(data)
    return " ".join(decoded)


def get_body_text(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            return payload.decode(charset, errors="replace")
    return ""


def parse_date(date_str):
    if not date_str:
        return None
    try:
        parsed = email.utils.parsedate_to_datetime(date_str)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except Exception:
        return None


# --- Index ---

def create_index(mbox_path, index_path):
    """Scan the mbox and build a SQLite index with byte offsets."""
    print(f"Building index from {mbox_path} ...", file=sys.stderr)
    index_path.parent.mkdir(parents=True, exist_ok=True)

    db = sqlite3.connect(str(index_path))
    db.execute("DROP TABLE IF EXISTS emails")
    db.execute("""
        CREATE TABLE emails (
            id INTEGER PRIMARY KEY,
            offset INTEGER NOT NULL,
            size INTEGER NOT NULL,
            date TEXT,
            date_utc TEXT,
            sender TEXT,
            subject TEXT
        )
    """)
    db.execute("CREATE INDEX idx_date ON emails(date_utc)")
    db.execute("CREATE INDEX idx_sender ON emails(sender)")
    db.execute("CREATE INDEX idx_subject ON emails(subject)")

    count = 0
    batch = []
    file_size = mbox_path.stat().st_size
    import time
    t_start = time.monotonic()

    with open(mbox_path, "rb") as f:
        offset = 0
        buf = []
        msg_offset = 0

        for line in f:
            if line.startswith(b"From ") and buf:
                raw = b"".join(buf)
                count += 1
                if count % 10000 == 0:
                    pct = offset * 100 / file_size
                    mb_read = offset / (1024 * 1024)
                    mb_total = file_size / (1024 * 1024)
                    elapsed = time.monotonic() - t_start
                    if pct > 0:
                        eta_secs = elapsed * (100 - pct) / pct
                        eta_min = int(eta_secs) // 60
                        eta_sec = int(eta_secs) % 60
                        eta_str = f", ETA {eta_min}:{eta_sec:02d}"
                    else:
                        eta_str = ""
                    print(f"  [{count} emails, {mb_read:.0f}/{mb_total:.0f} MB ({pct:.1f}%){eta_str}]", file=sys.stderr)

                try:
                    # Only parse headers for speed
                    header_end = raw.find(b"\n\n")
                    if header_end == -1:
                        header_end = raw.find(b"\r\n\r\n")
                    header_bytes = raw[:header_end] if header_end != -1 else raw[:4096]
                    msg = email.message_from_bytes(header_bytes)

                    date_raw = str(msg["Date"] or "")
                    date_parsed = parse_date(date_raw)
                    date_utc = date_parsed.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if date_parsed else None
                    sender = str(decode_header(msg["From"]))
                    subject = str(decode_header(msg["Subject"]))

                    batch.append((msg_offset, len(raw), date_raw, date_utc, sender, subject))
                except Exception:
                    batch.append((msg_offset, len(raw), None, None, "", ""))

                if len(batch) >= 5000:
                    db.executemany(
                        "INSERT INTO emails (offset, size, date, date_utc, sender, subject) VALUES (?, ?, ?, ?, ?, ?)",
                        batch,
                    )
                    db.commit()
                    batch = []

                buf = []
                msg_offset = offset

            buf.append(line)
            offset += len(line)

        # last message
        if buf:
            raw = b"".join(buf)
            count += 1
            try:
                header_end = raw.find(b"\n\n")
                if header_end == -1:
                    header_end = raw.find(b"\r\n\r\n")
                header_bytes = raw[:header_end] if header_end != -1 else raw[:4096]
                msg = email.message_from_bytes(header_bytes)

                date_raw = str(msg["Date"] or "")
                date_parsed = parse_date(date_raw)
                date_utc = date_parsed.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if date_parsed else None
                sender = str(decode_header(msg["From"]))
                subject = str(decode_header(msg["Subject"]))

                batch.append((msg_offset, len(raw), date_raw, date_utc, sender, subject))
            except Exception:
                batch.append((msg_offset, len(raw), None, None, "", ""))

    if batch:
        db.executemany(
            "INSERT INTO emails (offset, size, date, date_utc, sender, subject) VALUES (?, ?, ?, ?, ?, ?)",
            batch,
        )
    db.commit()
    db.close()
    print(f"Index complete: {count} emails indexed at {index_path}", file=sys.stderr)


def read_msg_at(mbox_path, offset, size):
    """Read and parse a single email from the mbox at the given offset."""
    with open(mbox_path, "rb") as f:
        f.seek(offset)
        raw = f.read(size)
    try:
        return email.message_from_bytes(raw)
    except Exception:
        return None


# --- Search ---

def search_index(args):
    db = sqlite3.connect(str(args.index_path))
    db.row_factory = sqlite3.Row

    conditions = []
    params = []

    if args.date_from:
        conditions.append("date_utc >= ?")
        params.append(args.date_from.strftime("%Y-%m-%d 00:00:00"))
    if args.date_to:
        conditions.append("date_utc < ?")
        params.append(args.date_to.strftime("%Y-%m-%d 00:00:00"))
    if args.sender:
        conditions.append("sender LIKE ? COLLATE NOCASE")
        params.append(f"%{args.sender}%")
    if args.subject:
        conditions.append("subject LIKE ? COLLATE NOCASE")
        params.append(f"%{args.subject}%")

    where = " AND ".join(conditions) if conditions else "1=1"
    order = "date_utc DESC"
    limit_clause = f"LIMIT {args.limit}" if not args.count and not args.body else ""

    query = f"SELECT * FROM emails WHERE {where} ORDER BY {order} {limit_clause}"
    rows = db.execute(query, params).fetchall()
    db.close()
    return rows


def show_email(mbox_path, index_path, email_id, output_format):
    """Show a single email by its database ID."""
    db = sqlite3.connect(str(index_path))
    db.row_factory = sqlite3.Row
    row = db.execute("SELECT * FROM emails WHERE id = ?", (email_id,)).fetchone()
    db.close()

    if row is None:
        print(f"Email with id {email_id} not found.", file=sys.stderr)
        sys.exit(1)

    msg = read_msg_at(mbox_path, row["offset"], row["size"])
    body = get_body_text(msg).strip() if msg else ""

    record = {
        "id": row["id"],
        "date": row["date"] or "(unknown)",
        "date_utc": row["date_utc"],
        "from": row["sender"],
        "subject": row["subject"],
        "body": body,
    }

    if output_format == "json":
        print(json.dumps(record, ensure_ascii=False, indent=2))
    elif output_format == "yaml":
        for key, val in record.items():
            if key == "body" and "\n" in val:
                print(f"{key}: |")
                for line in val.split("\n"):
                    print(f"  {line}")
            else:
                print(f"{key}: {val}")
    else:
        print(f"ID:      {record['id']}")
        print(f"Date:    {record['date']}")
        print(f"From:    {record['from']}")
        print(f"Subject: {record['subject']}")
        print(f"Body:\n{body}")


def format_result(row, body, found, output_format):
    """Format a single search result."""
    record = {
        "id": row["id"],
        "date": row["date"] or "(unknown)",
        "date_utc": row["date_utc"],
        "from": row["sender"],
        "subject": row["subject"],
    }
    if body is not None:
        record["body_preview"] = body[:500] if len(body) > 500 else body
        record["body_length"] = len(body)

    if output_format == "json":
        return json.dumps(record, ensure_ascii=False)
    elif output_format == "yaml":
        lines = []
        for key, val in record.items():
            lines.append(f"  {key}: {val}")
        return f"- \n" + "\n".join(lines)
    else:
        lines = [f"--- #{found} (id:{row['id']}) ---"]
        lines.append(f"Date:    {record['date']}")
        lines.append(f"From:    {record['from']}")
        lines.append(f"Subject: {record['subject']}")
        if body is not None:
            preview = body[:500].replace("\n", "\n         ")
            lines.append(f"Body:    {preview}")
            if len(body) > 500:
                lines.append(f"         [...{len(body)} chars total]")
        lines.append("")
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Search Google Takeout emails")
    parser.add_argument("--date-from", type=str, help="Start date (YYYY-MM-DD), inclusive")
    parser.add_argument("--date-to", type=str, help="End date (YYYY-MM-DD), exclusive")
    parser.add_argument("--from", dest="sender", type=str, help="Case-insensitive match on From header")
    parser.add_argument("--subject", type=str, help="Case-insensitive match on Subject")
    parser.add_argument("--body", type=str, help="Case-insensitive match in body text (needs mbox seek)")
    parser.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")
    parser.add_argument("--no-body", action="store_true", help="Don't show body preview")
    parser.add_argument("--count", action="store_true", help="Only count matches, don't print")
    parser.add_argument("--show", type=int, metavar="ID", help="Show full email by database ID")
    parser.add_argument("--output", type=str, default="text", choices=["text", "json", "yaml"],
                        help="Output format (default: text)")
    parser.add_argument("--re-index", action="store_true", help="Force rebuild the index")
    parser.add_argument("--mbox", type=str, default=str(MBOX_PATH), help="Path to mbox file")
    args = parser.parse_args()

    mbox_path = Path(args.mbox)
    args.index_path = mbox_path.parent / "index.sqlite"

    if args.re_index or not args.index_path.exists():
        create_index(mbox_path, args.index_path)
        if args.re_index and not (args.show is not None or args.date_from or args.date_to or args.sender or args.subject or args.body):
            return

    # Show single email by ID
    if args.show is not None:
        show_email(mbox_path, args.index_path, args.show, args.output)
        return

    if args.date_from:
        args.date_from = datetime.strptime(args.date_from, "%Y-%m-%d")
    if args.date_to:
        args.date_to = datetime.strptime(args.date_to, "%Y-%m-%d")

    rows = search_index(args)

    if args.output == "json" and not args.count:
        results = []

    found = 0
    for row in rows:
        # If body filter requested, seek into mbox and check
        if args.body:
            msg = read_msg_at(mbox_path, row["offset"], row["size"])
            if msg is None:
                continue
            body_text = get_body_text(msg).lower()
            if args.body.lower() not in body_text:
                continue

        found += 1
        body = None
        if not args.count and not args.no_body:
            msg = read_msg_at(mbox_path, row["offset"], row["size"])
            body = get_body_text(msg).strip() if msg else ""

        if not args.count:
            if args.output == "json":
                record = {
                    "id": row["id"],
                    "date": row["date"] or "(unknown)",
                    "date_utc": row["date_utc"],
                    "from": row["sender"],
                    "subject": row["subject"],
                }
                if body is not None:
                    record["body_preview"] = body[:500]
                    record["body_length"] = len(body)
                results.append(record)
            else:
                print(format_result(row, body, found, args.output))
                sys.stdout.flush()

        if not args.count and found >= args.limit:
            break

    if args.count:
        if args.output == "json":
            print(json.dumps({"count": found}))
        else:
            print(f"{found} matches")
    elif args.output == "json" and not args.count:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    elif found == 0:
        print("No matches found.", file=sys.stderr)


if __name__ == "__main__":
    main()
