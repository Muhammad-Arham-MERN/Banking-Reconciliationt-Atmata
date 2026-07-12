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
