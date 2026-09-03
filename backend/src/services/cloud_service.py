# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Cloud database service for reconciliation data persistence.
All DB operations use raw asyncpg via db_service — no SQLModel.
"""
import logging
import json
from src.services.db_service import db_service

logger = logging.getLogger(__name__)


async def get_user_files(user_id: int) -> list[str]:
    """Retrieve file names from users.files JSONB column for the given user."""
    row = await db_service.fetchrow(
        "SELECT files FROM users WHERE id = $1", user_id
    )
    if row and row["files"]:
        raw = row["files"]
        # CockroachDB JSONB returns as string via asyncpg by default
        if isinstance(raw, str):
            return json.loads(raw)
        return raw
    return []


def _decode_jsonb(value) -> list:
    """CockroachDB JSONB arrives as a string via asyncpg — decode defensively."""
    if value is None:
        return []
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return []
    return value


def _encode_jsonb(value: list) -> str:
    return json.dumps(value)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def get_user_files_meta(user_id: int) -> list[dict]:
    """Metadata for every stored past file (newest first)."""
    rows = await db_service.fetch(
        """
        SELECT id, file_name, created_at, reconciliation_type,
               jsonb_array_length(data) AS entry_count
        FROM reconciliation_data
        WHERE user_id = $1
        ORDER BY created_at DESC, id DESC
        """,
        user_id,
    )
    result = []
    for row in rows:
        created = row.get("created_at")
        result.append({
            # Stringified — CockroachDB SERIAL ids exceed JS safe-integer range.
            "file_id": str(row["id"]),
            "file_name": row["file_name"],
            "created_at": created.isoformat() if hasattr(created, "isoformat") else str(created),
            "entry_count": row.get("entry_count") or 0,
            "reconciliation_type": row.get("reconciliation_type") or "bank",
        })
    return result


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def get_reconciliation(user_id: int, file_id: int) -> dict | None:
    """Fetch one stored past file, scoped to the authenticated user."""
    row = await db_service.fetchrow(
        """
        SELECT id, file_name, data, reconciliation_type
        FROM reconciliation_data
        WHERE id = $1 AND user_id = $2
        """,
        file_id, user_id,
    )
    if not row:
        return None
    return {
        "file_id": str(row["id"]),
        "file_name": row["file_name"],
        "reconciliation_type": row.get("reconciliation_type") or "bank",
        "discrepancies": _decode_jsonb(row["data"]),
    }


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def load_reconciliation_by_name(user_id: int, file_name: str) -> dict | None:
    """
    Fetch one stored past file by file name, scoped to the authenticated user.
    Used when merging a past file's discrepancies into a new reconciliation.
    """
    row = await db_service.fetchrow(
        """
        SELECT id, file_name, data, reconciliation_type
        FROM reconciliation_data
        WHERE file_name = $1 AND user_id = $2
        """,
        file_name, user_id,
    )
    if not row:
        return None
    return {
        "file_id": str(row["id"]),
        "file_name": row["file_name"],
        "reconciliation_type": row.get("reconciliation_type") or "bank",
        "discrepancies": _decode_jsonb(row["data"]),
    }


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def create_reconciliation(
    user_id: int, file_name: str, reconciliation_type: str, file_data: list[dict]
) -> int:
    """Create a new past file and register its name for the user."""
    row = await db_service.fetchrow(
        """
        INSERT INTO reconciliation_data (file_name, data, user_id, reconciliation_type)
        VALUES ($1, $2::jsonb, $3, $4)
        RETURNING id
        """,
        file_name, _encode_jsonb(file_data), user_id, reconciliation_type,
    )
    new_id = row["id"]
    await db_service.execute(
        "UPDATE users SET files = files || $1::jsonb WHERE id = $2",
        _encode_jsonb([file_name]), user_id,
    )
    logger.info("Created past reconciliation record: %s (id=%s)", file_name, new_id)
    return new_id


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def update_reconciliation(
    user_id: int,
    file_id: int,
    file_name: str | None = None,
    file_data: list[dict] | None = None,
) -> dict | None:
    """
    Update a stored past file's data and/or name. On rename, the old name is
    replaced inside the user's `users.files` list (read-modify-write, keeps order).
    Returns the refreshed file or None if it does not belong to the user.
    """
    existing = await db_service.fetchrow(
        "SELECT file_name, data FROM reconciliation_data WHERE id = $1 AND user_id = $2",
        file_id, user_id,
    )
    if not existing:
        return None

    old_name = existing["file_name"]
    new_name = file_name if file_name is not None else old_name
    new_data = file_data if file_data is not None else _decode_jsonb(existing["data"])

    await db_service.execute(
        "UPDATE reconciliation_data SET file_name = $1, data = $2::jsonb WHERE id = $3",
        new_name, _encode_jsonb(new_data), file_id,
    )

    if new_name != old_name:
        names = await get_user_files(user_id)
        if old_name in names:
            names[names.index(old_name)] = new_name
        else:
            names.append(new_name)
        await db_service.execute(
            "UPDATE users SET files = $1::jsonb WHERE id = $2",
            _encode_jsonb(names), user_id,
        )

    logger.info("Updated past reconciliation record: %s (id=%s)", new_name, file_id)
    return {
        "file_id": str(file_id),
        "file_name": new_name,
        "reconciliation_type": (await db_service.fetchrow(
            "SELECT reconciliation_type FROM reconciliation_data WHERE id = $1",
            file_id,
        ))["reconciliation_type"] or "bank",
        "discrepancies": new_data,
    }


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def delete_reconciliation(user_id: int, file_id: int) -> str | None:
    """
    Delete a stored past file. Removes its name from `users.files` and returns
    the deleted file name (or None if the file did not belong to the user).
    """
    row = await db_service.fetchrow(
        "SELECT file_name FROM reconciliation_data WHERE id = $1 AND user_id = $2",
        file_id, user_id,
    )
    if not row:
        return None

    file_name = row["file_name"]
    await db_service.execute(
        "DELETE FROM reconciliation_data WHERE id = $1 AND user_id = $2",
        file_id, user_id,
    )

    names = await get_user_files(user_id)
    if file_name in names:
        names.remove(file_name)
        await db_service.execute(
            "UPDATE users SET files = $1::jsonb WHERE id = $2",
            _encode_jsonb(names), user_id,
        )

    logger.info("Deleted past reconciliation record: %s (id=%s)", file_name, file_id)
    return file_name


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def save_reconciliation(
    user_id: int, file_name: str, file_data: list[dict]
) -> None:
    """
    Upsert a reconciliation record and sync users.files for new records.
    Uses raw asyncpg queries — no SQLModel dependency.
    """
    # Check if record exists for this user
    existing = await db_service.fetchrow(
        "SELECT id FROM reconciliation_data WHERE file_name = $1 AND user_id = $2",
        file_name, user_id,
    )

    if existing:
        # Upsert: update existing record's data
        await db_service.execute(
            "UPDATE reconciliation_data SET data = $1 WHERE id = $2",
            json.dumps(file_data), existing["id"],
        )
        logger.info("Upserted existing reconciliation record: %s", file_name)
    else:
        # Insert: create new record
        await db_service.execute(
            "INSERT INTO reconciliation_data (file_name, data, user_id) VALUES ($1, $2::jsonb, $3)",
            file_name, json.dumps(file_data), user_id,
        )
        logger.info("Created new reconciliation record: %s", file_name)

        # Append file_name to users.files for new records
        await db_service.execute(
            "UPDATE users SET files = files || $1::jsonb WHERE id = $2",
            json.dumps([file_name]), user_id,
        )

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
