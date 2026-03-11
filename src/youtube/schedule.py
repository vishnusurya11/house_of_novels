"""
Schedule Database — Claim and release YouTube upload time slots.

Connects to the shared visurena_studio.db SQLite database to manage
scheduled publishing times for per-chapter audiobook uploads.

Table schema:
    schedule(env TEXT, time_slot TEXT, type TEXT, book_id TEXT, book_name TEXT, part INTEGER)
    PRIMARY KEY (env, time_slot, type)
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from src.config import SCHEDULE_DB_PATH, ENVIRONMENT


def _connect() -> sqlite3.Connection:
    """Open a connection to the schedule database."""
    if not SCHEDULE_DB_PATH.exists():
        raise FileNotFoundError(f"Schedule database not found: {SCHEDULE_DB_PATH}")
    return sqlite3.connect(str(SCHEDULE_DB_PATH))


def time_slot_to_datetime(time_slot: str) -> datetime:
    """Parse a time_slot string to a timezone-aware UTC datetime.

    Supports formats:
        YYYYMMDDHHMMSS (14 chars)
        YYYYMMDDHHMM   (12 chars)
        YYYYMMDDHH     (10 chars)

    Args:
        time_slot: Time slot string from the schedule table.

    Returns:
        Timezone-aware datetime in UTC.
    """
    ts = time_slot.strip()
    if len(ts) == 14:
        dt = datetime.strptime(ts, "%Y%m%d%H%M%S")
    elif len(ts) == 12:
        dt = datetime.strptime(ts, "%Y%m%d%H%M")
    elif len(ts) == 10:
        dt = datetime.strptime(ts, "%Y%m%d%H")
    else:
        raise ValueError(f"Unrecognised time_slot format: {time_slot!r}")
    return dt.replace(tzinfo=timezone.utc)


def claim_slots(
    book_id: str,
    book_name: str,
    num_chapters: int,
    env: str | None = None,
) -> list[dict]:
    """Claim the next available time slots for a book's chapters.

    Finds `num_chapters` unassigned slots (book_id IS NULL) for the given
    environment and type='audiobook', ordered by time_slot ascending, then
    atomically assigns them.

    Args:
        book_id: Unique book identifier (typically the forge timestamp).
        book_name: Human-readable book/story title.
        num_chapters: Number of slots to claim (one per chapter).
        env: Environment filter ('alpha' or 'prod'). Defaults to auto-detected.

    Returns:
        List of dicts with keys: part, time_slot, publish_at (ISO 8601 string).
        Empty list if not enough slots are available.
    """
    env = env or ENVIRONMENT
    conn = _connect()
    try:
        cursor = conn.cursor()

        # Find available slots
        cursor.execute(
            "SELECT time_slot FROM schedule "
            "WHERE book_id IS NULL AND env = ? AND type = 'audiobook' "
            "ORDER BY time_slot "
            "LIMIT ?",
            (env, num_chapters),
        )
        rows = cursor.fetchall()

        if len(rows) < num_chapters:
            print(f">>> Warning: Only {len(rows)} slots available, need {num_chapters}")
            if not rows:
                return []

        # Claim each slot
        results = []
        for i, (slot,) in enumerate(rows, start=1):
            cursor.execute(
                "UPDATE schedule SET book_id = ?, book_name = ?, part = ? "
                "WHERE env = ? AND time_slot = ? AND type = 'audiobook'",
                (book_id, book_name, i, env, slot),
            )
            publish_dt = time_slot_to_datetime(slot)
            results.append({
                "part": i,
                "time_slot": slot,
                "publish_at": publish_dt.isoformat(),
            })

        conn.commit()
        print(f">>> Claimed {len(results)} schedule slots for '{book_name}' in {env}")
        return results

    finally:
        conn.close()


def release_slots(book_id: str, env: str | None = None) -> int:
    """Release all slots claimed by a book (rollback on failure).

    Args:
        book_id: The book identifier whose slots to release.
        env: Environment filter. Defaults to auto-detected.

    Returns:
        Number of slots released.
    """
    env = env or ENVIRONMENT
    conn = _connect()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE schedule SET book_id = NULL, book_name = NULL, part = NULL "
            "WHERE book_id = ? AND env = ? AND type = 'audiobook'",
            (book_id, env),
        )
        released = cursor.rowcount
        conn.commit()
        if released:
            print(f">>> Released {released} schedule slots for book_id={book_id}")
        return released
    finally:
        conn.close()
