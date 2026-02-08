"""File-based context journal for Daily AI Assistant.

No vector store, no embeddings. Simple append-only JSON journal with UTC timestamps.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Optional

DEFAULT_JOURNAL_PATH = Path(__file__).parent.parent / "daily_context.json"


def init_journal(path: Optional[str | Path] = None) -> Path:
    """Initialize a new context journal file with [] if it does not exist.

    Args:
        path: Optional path to journal file. Defaults to daily_context.json in project root.

    Returns:
        Path to the journal file.
    """
    journal_path = Path(path) if path else DEFAULT_JOURNAL_PATH
    if not journal_path.exists():
        journal_path.write_text("[]", encoding="utf-8")
    return journal_path


def add_context(
    doc_text: str,
    entry_type: str = "text",
    source: str = "user",
    path: Optional[str | Path] = None,
    fact_status: Optional[str] = None,
) -> None:
    """Append a new context entry to the journal with timestamp.

    Args:
        doc_text: Raw text added by the user. Must be non-empty when trimmed.
        entry_type: A simple category (e.g., "text", "email", "court_note", "phone_call", "other").
        source: Origin of the text (e.g., "user", "dashboard", "cli").
        path: Optional path to journal file.
        fact_status: Optional classification: REALISED / EVIDENCED / ALLEGED / PROSPECTIVE

    Raises:
        ValueError: If doc_text is empty or whitespace-only.
    """
    text_stripped = doc_text.strip()
    if not text_stripped:
        raise ValueError("Context text cannot be empty or whitespace-only.")

    # Validate fact_status if provided
    if fact_status and fact_status not in ("REALISED", "EVIDENCED", "ALLEGED", "PROSPECTIVE"):
        raise ValueError(f"Invalid fact_status: {fact_status}. Must be REALISED, EVIDENCED, ALLEGED, or PROSPECTIVE.")

    journal_path = Path(path) if path else DEFAULT_JOURNAL_PATH
    init_journal(journal_path)

    entry = {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "entry_type": entry_type,
        "source": source,
        "text": text_stripped,
        "fact_status": fact_status,
    }

    # Atomic write: read current, append, write to temp, then rename
    with open(journal_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data.append(entry)

    # Write to temp file in same directory, then rename for atomicity
    temp_fd, temp_path = tempfile.mkstemp(
        dir=journal_path.parent,
        prefix="daily_context_tmp_",
        suffix=".json",
    )
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, journal_path)
    except Exception:
        # Clean up temp file if something went wrong
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass
        raise


def read_entries(path: Optional[str | Path] = None) -> list[dict]:
    """Read all entries from the journal.

    Args:
        path: Optional path to journal file.

    Returns:
        List of entry dictionaries. Returns empty list if file doesn't exist.
    """
    journal_path = Path(path) if path else DEFAULT_JOURNAL_PATH
    if not journal_path.exists():
        return []
    with open(journal_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_all_context(
    path: Optional[str | Path] = None,
    limit: Optional[int] = None,
) -> str:
    """Read the entire journal and return a single concatenated string of all entries.

    Args:
        path: Optional path to journal file.
        limit: Optional maximum number of most recent entries to include.
               If None (default), includes ALL entries.

    Returns:
        Concatenated string of all entry texts in chronological order,
        separated by newlines. Returns empty string if no entries.
    """
    entries = read_entries(path)
    if not entries:
        return ""

    if limit is not None and limit > 0:
        entries = entries[-limit:]

    def format_entry(e: dict) -> str:
        status_tag = f" [{e.get('fact_status')}]" if e.get('fact_status') else ""
        return f"[{e['timestamp_utc']}] [{e['entry_type']}]{status_tag} {e['text']}"

    return "\n\n---\n\n".join(format_entry(e) for e in entries)
