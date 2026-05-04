import csv
import io
import re

from email_validator import EmailNotValidError, validate_email

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_and_validate_email(raw: str) -> str | None:
    raw = raw.strip().lower()
    if not raw:
        return None
    try:
        v = validate_email(raw, check_deliverability=False)
        return v.normalized
    except EmailNotValidError:
        return None


def parse_emails_csv(content: bytes) -> tuple[list[str], int]:
    """Parse single-column CSV (header optional: email). Returns (deduplicated valid emails, invalid count)."""
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.reader(io.StringIO(text))
    seen: set[str] = set()
    out: list[str] = []
    invalid = 0
    for row in reader:
        if not row:
            continue
        cell = row[0].strip()
        if cell.lower() in ("email", "e-mail"):
            continue
        email = normalize_and_validate_email(cell)
        if not email and cell:
            invalid += 1
            continue
        if email and email not in seen:
            seen.add(email)
            out.append(email)
    return out, invalid
