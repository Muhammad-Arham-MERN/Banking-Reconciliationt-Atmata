# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
PDF structure profiles store (Judge Structure by its Cover).

Persists previously-extracted PDF structures keyed by normalized entity name +
entity type ("bank" | "vendor"), so the Judge agent can short-circuit full
structure detection on repeat uploads from the same bank/vendor.

Raw asyncpg via the existing DatabaseService (project taste: no SQLModel).
Every method is FAIL-OPEN: a DB error is logged and the caller receives the
safe default (empty list / None / no-op) so the Judge and the persistence hook
degrade gracefully and never crash a reconciliation run.
"""
import logging
import re
from typing import Any, Dict, List, Optional

from src.services.db_service import db_service

logger = logging.getLogger(__name__)

# Valid entity types (same concept as reconciliation_type).
VALID_ENTITY_TYPES = ("bank", "vendor")


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def normalize_entity_name(name: str) -> str:
    """Normalize an entity name for unique-key matching.

    Lowercases, strips non-alphanumeric characters, and collapses whitespace,
    so "Askari Bank" and "askari bank" (and "Askar Bank" / "askari_bank")
    normalize to the same key. Mirrors the _normalize pattern used in
    ai_pdf_processor.py.
    """
    if not name:
        return ""
    lowered = name.strip().lower()
    # Replace every run of non-alphanumeric characters with a single space,
    # then trim: "Askari Bank (Pvt) Ltd." -> "askari bank pvt ltd".
    collapsed = re.sub(r"[^a-z0-9]+", " ", lowered)
    return collapsed.strip()


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _is_valid_type(entity_type: str) -> bool:
    return entity_type in VALID_ENTITY_TYPES


async def list_profiles(entity_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return the compact list of known entities.

    Each entry is {entity_name, entity_type} only - deliberately context-tiny
    so the Judge can see the full catalog without bloating the LLM context
    (taste: context-bloat control). When entity_type is given, only profiles
    of that type are returned.

    Fail-open: returns [] on any DB error.
    """
    try:
        if entity_type:
            if not _is_valid_type(entity_type):
                return []
            rows = await db_service.fetch(
                "SELECT entity_name, entity_type FROM pdf_structure_profiles "
                "WHERE entity_type = $1 ORDER BY entity_name",
                entity_type,
            )
        else:
            rows = await db_service.fetch(
                "SELECT entity_name, entity_type FROM pdf_structure_profiles "
                "ORDER BY entity_name"
            )
        return [
            {"entity_name": r["entity_name"], "entity_type": r["entity_type"]}
            for r in rows
        ]
    except Exception as e:
        logger.warning("list_profiles failed (fail-open -> []): %s", e)
        return []


async def get_profile(entity_name: str, entity_type: str) -> Optional[Dict[str, Any]]:
    """Return the full stored structure for an entity, or None when absent.

    Matched by NORMALIZED name + entity type (case/punctuation-insensitive).
    The returned dict carries {entity_name, entity_type, structure, updated_at}
    where `structure` is the parsed FileStructureOutput dict.

    Fail-open: returns None on any DB error.
    """
    try:
        if not _is_valid_type(entity_type):
            return None
        normalized = normalize_entity_name(entity_name)
        if not normalized:
            return None
        row = await db_service.fetchrow(
            "SELECT entity_name, entity_type, structure, updated_at "
            "FROM pdf_structure_profiles "
            "WHERE entity_name_normalized = $1 AND entity_type = $2",
            normalized,
            entity_type,
        )
        if row is None:
            return None
        return {
            "entity_name": row["entity_name"],
            "entity_type": row["entity_type"],
            "structure": row["structure"],
            "updated_at": row["updated_at"],
        }
    except Exception as e:
        logger.warning("get_profile failed (fail-open -> None): %s", e)
        return None


async def upsert_profile(
    entity_name: str,
    entity_type: str,
    structure: Dict[str, Any],
) -> None:
    """Insert or update the stored structure for an entity.

    ON CONFLICT on (entity_name_normalized, entity_type) updates the structure
    in place and bumps updated_at, so a bank that changed its layout gets its
    profile refreshed on the next fully-passing extraction.

    Fail-open: logs and returns on any DB error - a store failure must never
    fail the reconciliation (fire-and-log).
    """
    try:
        if not _is_valid_type(entity_type):
            logger.warning("upsert_profile skipped: invalid entity_type %r", entity_type)
            return
        normalized = normalize_entity_name(entity_name)
        if not normalized:
            logger.warning("upsert_profile skipped: empty entity name")
            return
        await db_service.execute(
            "INSERT INTO pdf_structure_profiles "
            "(entity_name, entity_name_normalized, entity_type, structure) "
            "VALUES ($1, $2, $3, $4::jsonb) "
            "ON CONFLICT (entity_name_normalized, entity_type) "
            "DO UPDATE SET structure = EXCLUDED.structure, updated_at = NOW()",
            entity_name.strip(),
            normalized,
            entity_type,
            _json_dumps(structure),
        )
        logger.info("Upserted pdf structure profile for %r (%s)", entity_name, entity_type)
    except Exception as e:
        logger.warning("upsert_profile failed (fail-open, no-op): %s", e)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _json_dumps(value: Any) -> str:
    import json

    try:
        return json.dumps(value, default=str)
    except Exception:
        return "{}"


# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
