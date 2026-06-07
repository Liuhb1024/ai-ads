import aiosqlite
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "ai-ad.db"

AD_COLUMN_MIGRATIONS = {
    "ad_title": "TEXT",
    "product_name": "TEXT",
    "price_range": "TEXT",
    "ad_copy": "TEXT",
    "scene_description": "TEXT",
    "screenshot_description": "TEXT",
    "user_context": "TEXT",
    "seen_at": "TEXT",
    "analysis_json": "TEXT",
    "error_message": "TEXT",
    "source_text": "TEXT",
    "source_url": "TEXT",
    "source_platform": "TEXT",
    "parsed_title": "TEXT",
    "parsed_author": "TEXT",
    "thumbnail_url": "TEXT",
    "source_metadata_json": "TEXT",
    "workflow_stage": "TEXT NOT NULL DEFAULT 'pending'",
    "progress_message": "TEXT",
    "missing_fields_json": "TEXT",
    "media_path": "TEXT",
    "transcript_json": "TEXT",
    "frames_json": "TEXT",
    "publishing_json": "TEXT",
    "failed_stage": "TEXT",
    "video_status": "TEXT DEFAULT ''",
    "video_path": "TEXT DEFAULT ''",
}


async def get_db():
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()


async def init_db(db_path: Path | str = DB_PATH):
    target = Path(db_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(str(target))
    db.row_factory = aiosqlite.Row

    await db.executescript("""
        CREATE TABLE IF NOT EXISTS ads (
            id          TEXT PRIMARY KEY,
            status      TEXT NOT NULL DEFAULT 'pending',

            -- User input fields
            ad_title            TEXT,
            brand_name          TEXT NOT NULL,
            product_name        TEXT,
            industry            TEXT NOT NULL,
            price_range         TEXT,
            ad_copy             TEXT,
            scene_description   TEXT,
            screenshot_description TEXT,
            user_context        TEXT,
            seen_at             TEXT,
            platform            TEXT NOT NULL,

            -- Analysis result (JSON string)
            analysis_json   TEXT,

            -- Error info
            error_message   TEXT,

            -- Timestamps
            created_at   TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_ads_status ON ads(status);
        CREATE INDEX IF NOT EXISTS idx_ads_created_at ON ads(created_at DESC);
    """)

    cursor = await db.execute("PRAGMA table_info(ads)")
    existing_columns = {row[1] for row in await cursor.fetchall()}
    for column, definition in AD_COLUMN_MIGRATIONS.items():
        if column not in existing_columns:
            await db.execute(f"ALTER TABLE ads ADD COLUMN {column} {definition}")

    await db.commit()
    await db.close()
