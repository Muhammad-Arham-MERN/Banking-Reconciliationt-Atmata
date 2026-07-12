# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
"""
History Service
Manages saving, listing, and loading reconciliation history
"""
import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.services.db_service import db_service

logger = logging.getLogger(__name__)

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
class HistoryService:
    """Service for managing reconciliation history SQLite files"""

    def __init__(self):
        """Initialize history service with project-root history directory"""
        # Resolve project root: backend/src/services/history_service.py -> ../../
        self.service_dir = Path(__file__).resolve().parent
        self.backend_dir = self.service_dir.parent.parent  # backend/
        self.project_root = self.backend_dir.parent  # project root
        self.history_dir = self.project_root / "Reconciliation History"
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_filename(self, name: str) -> str:
        """Clean a filename to prevent path traversal"""
        # Remove extension if accidentally provided
        if name.lower().endswith('.sqlite'):
            name = name[:-7]
        # Remove path separators and dangerous chars
        clean = "".join(c for c in name if c.isalnum() or c in " _.-")
        return clean.strip()

    def _generate_default_name(self) -> str:
        """Generate a date-time based filename"""
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    def _get_file_path(self, file_name: str) -> Path:
        """Get full path for a history file"""
        sanitized = self._sanitize_filename(file_name)
        return self.history_dir / f"{sanitized}.sqlite"

    # وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
    def save_history(self, name: Optional[str], discrepancies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Save discrepancy entries to a new SQLite history file.

        Args:
            name: Optional custom name (auto-generated if None)
            discrepancies: List of discrepancy dicts with category, transaction_details,
                          transaction_date, debit_credit_amount

        Returns:
            Dict with status, file_name, entry_count, message

        Raises:
            ValueError: If name collision occurs or discrepancies are empty
        """
        if not discrepancies:
            raise ValueError("Cannot save: no discrepancies to save")

        # Determine filename
        if name:
            file_name = self._sanitize_filename(name)
        else:
            file_name = self._generate_default_name()

        file_path = self._get_file_path(file_name)

        # Check collision (only for user-provided names)
        if name and file_path.exists():
            raise ValueError(
                f"A file with the name '{file_name}' already exists. "
                f"Please choose a different name."
            )

        # Ensure unique auto-generated names
        counter = 0
        while file_path.exists():
            counter += 1
            file_path = self._get_file_path(f"{file_name}_{counter}")

        # Create and populate SQLite database
        conn = sqlite3.connect(str(file_path))
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS discrepancies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL CHECK (category IN (
                        'Unpresented Checks',
                        'Uncleared Checks',
                        'Bank Debited But not Credited in Cashbook',
                        'Bank Credited But not Debited in Cashbook'
                    )),
                    transaction_details TEXT NOT NULL,
                    transaction_date TEXT NOT NULL,
                    debit_credit_amount REAL NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON discrepancies(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_date ON discrepancies(transaction_date)")

            # Insert entries
            for entry in discrepancies:
                category = entry.get("category", "")
                cursor.execute(
                    """INSERT INTO discrepancies (category, transaction_details, transaction_date, debit_credit_amount)
                       VALUES (?, ?, ?, ?)""",
                    (
                        category,
                        entry.get("transaction_details", ""),
                        entry.get("transaction_date", ""),
                        entry.get("debit_credit_amount", 0.0)
                    )
                )

            conn.commit()
            entry_count = len(discrepancies)
            actual_file_name = file_path.name

            logger.info(f"Saved {entry_count} discrepancies to {file_path}")

            return {
                "status": "saved",
                "file_name": actual_file_name,
                "entry_count": entry_count,
                "message": f"Saved {entry_count} discrepancies to {actual_file_name}"
            }

        except sqlite3.Error as e:
            logger.error(f"SQLite error saving history: {str(e)}")
            raise RuntimeError(f"Failed to save history: {str(e)}")
        finally:
            conn.close()

    # وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
    def list_history(self) -> Dict[str, Any]:
        """
        List all saved history SQLite files in the Reconciliation History directory.

        Returns:
            Dict with files array (file_name, file_path, created_at, entry_count) and total count
        """
        files = []
        if not self.history_dir.exists():
            return {"files": [], "total": 0, "message": "No reconciliation history found."}

        for f in sorted(self.history_dir.glob("*.sqlite"), key=lambda p: p.stat().st_mtime, reverse=True):
            # Count entries in the file
            entry_count = 0
            try:
                conn = sqlite3.connect(str(f))
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM discrepancies")
                entry_count = cursor.fetchone()[0]
                conn.close()
            except sqlite3.Error:
                pass  # Corrupted file — entry_count stays 0

            files.append({
                "file_name": f.name,
                "file_path": str(f.relative_to(self.project_root)),
                "created_at": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                "entry_count": entry_count
            })

        return {"files": files, "total": len(files)}

    # وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
    async def load_history(self, file_name: str) -> Dict[str, Any]:
        """
        Load discrepancy entries from CockroachDB via asyncpg.

        Args:
            file_name: Filename of the reconciliation record

        Returns:
            Dict with status, file_name, discrepancies array, entry_count

        Raises:
            FileNotFoundError: If the record doesn't exist
            RuntimeError: If the data is malformed
        """
        row = await db_service.fetchrow(
            "SELECT file_name, data FROM reconciliation_data WHERE file_name = $1",
            file_name,
        )

        if not row:
            raise FileNotFoundError(
                f"History record '{file_name}' not found in cloud database."
            )

        file_data = row["data"]
        # CockroachDB JSONB returns as string via asyncpg by default
        if isinstance(file_data, str):
            try:
                file_data = json.loads(file_data)
            except json.JSONDecodeError:
                logger.error(
                    "Malformed JSON data for record '%s': %s",
                    file_name, file_data[:200],
                )
                raise RuntimeError(
                    f"History record '{file_name}' contains invalid JSON data. "
                    f"Proceeding with current reconciliation only."
                )
        if not isinstance(file_data, list):
            logger.error(
                "Malformed data for record '%s': expected list, got %s",
                file_name, type(file_data).__name__,
            )
            raise RuntimeError(
                f"History record '{file_name}' contains invalid data. "
                f"Proceeding with current reconciliation only."
            )

        discrepancies = []
        for entry in file_data:
            discrepancies.append({
                "category": entry.get("category", ""),
                "transaction_details": entry.get("transaction_details", ""),
                "transaction_date": entry.get("transaction_date", ""),
                "debit_credit_amount": entry.get("debit_credit_amount", 0.0),
                "from_past": True,
            })

        return {
            "status": "loaded",
            "file_name": file_name,
            "discrepancies": discrepancies,
            "entry_count": len(discrepancies),
        }

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
