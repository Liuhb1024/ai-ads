import asyncio
import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.database import init_db


EXPECTED_JOB_COLUMNS = {
    "source_text",
    "source_url",
    "source_platform",
    "parsed_title",
    "parsed_author",
    "thumbnail_url",
    "source_metadata_json",
    "workflow_stage",
    "progress_message",
    "missing_fields_json",
    "media_path",
    "transcript_json",
    "frames_json",
    "publishing_json",
    "failed_stage",
}


class DatabaseMigrationTests(unittest.TestCase):
    def test_additive_migration_preserves_existing_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "legacy.db"
            conn = sqlite3.connect(db_path)
            conn.execute(
                """
                CREATE TABLE ads (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    brand_name TEXT NOT NULL,
                    industry TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "INSERT INTO ads VALUES ('legacy01', 'completed', '旧品牌', '美妆', '抖音', 'now', 'now')"
            )
            conn.commit()
            conn.close()

            asyncio.run(init_db(db_path))

            conn = sqlite3.connect(db_path)
            columns = {row[1] for row in conn.execute("PRAGMA table_info(ads)")}
            count = conn.execute("SELECT COUNT(*) FROM ads WHERE id = 'legacy01'").fetchone()[0]
            conn.close()

            self.assertTrue(EXPECTED_JOB_COLUMNS.issubset(columns))
            self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()
