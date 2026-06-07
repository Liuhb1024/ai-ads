import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

import aiosqlite
from fastapi.testclient import TestClient

from app.database import get_db, init_db
from app.main import app


SHARE_TEXT = "广告案例 https://v.douyin.com/zQB8XLGqE4I/ 复制打开抖音"


class JobsApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "jobs.db"
        asyncio.run(init_db(self.db_path))

        async def override_db():
            db = await aiosqlite.connect(str(self.db_path))
            db.row_factory = aiosqlite.Row
            try:
                yield db
            finally:
                await db.close()

        app.dependency_overrides[get_db] = override_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.tmp.cleanup()

    def test_full_share_message_creates_job_without_manual_fields(self):
        with patch("app.routers.ads.run_job", new=AsyncMock()) as worker:
            response = self.client.post("/api/jobs", json={"share_text": SHARE_TEXT})

        self.assertEqual(response.status_code, 202)
        body = response.json()
        self.assertEqual(body["status"], "analyzing")
        self.assertEqual(body["stage"], "resolving")
        self.assertEqual(body["next_url"], f"/jobs/{body['id']}")
        worker.assert_awaited_once_with(body["id"])

    def test_rejects_share_text_without_supported_url(self):
        response = self.client.post("/api/jobs", json={"share_text": "没有链接"})
        self.assertEqual(response.status_code, 422)
        self.assertIn("没有识别到有效链接", response.json()["detail"])

    def test_completed_job_exports_markdown_and_pdf(self):
        async def seed():
            async with aiosqlite.connect(str(self.db_path)) as db:
                await db.execute(
                    """INSERT INTO ads (
                        id, status, brand_name, product_name, industry, platform,
                        source_platform, analysis_json, publishing_json, created_at, updated_at
                    ) VALUES (?, 'completed', ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        "export01",
                        "元气森林",
                        "好自在",
                        "食品",
                        "抖音",
                        "抖音",
                        json.dumps(
                            {
                                "analysis_meta": {"trust_score": 88, "audit_verdict": "pass"},
                                "material_understanding": {"evidence_ledger": []},
                                "quality_audit": {"trust_score": 88, "verdict": "pass"},
                                "final_note": {"one_sentence_takeaway": "一句话洞察"},
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps({}, ensure_ascii=False),
                        "2026-06-07 12:00:00",
                        "2026-06-07 12:00:00",
                    ),
                )
                await db.commit()

        asyncio.run(seed())

        markdown = self.client.get("/api/jobs/export01/export.md")
        self.assertEqual(markdown.status_code, 200)
        self.assertIn("text/markdown", markdown.headers["content-type"])
        self.assertIn("广告创意研究报告", markdown.text)

        pdf = self.client.get("/api/jobs/export01/export.pdf")
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf.headers["content-type"], "application/pdf")
        self.assertTrue(pdf.content.startswith(b"%PDF"))

    def test_completed_job_detail_rebuilds_full_markdown_report(self):
        async def seed():
            async with aiosqlite.connect(str(self.db_path)) as db:
                await db.execute(
                    """INSERT INTO ads (
                        id, status, brand_name, product_name, industry, platform,
                        source_platform, analysis_json, publishing_json, created_at, updated_at
                    ) VALUES (?, 'completed', ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        "detail01",
                        "元气森林",
                        "好自在",
                        "食品",
                        "抖音",
                        "抖音",
                        json.dumps(
                            {
                                "analysis_meta": {"trust_score": 80, "audit_verdict": "pass"},
                                "material_understanding": {
                                    "product_summary": {"usp": "多口味大包装"},
                                    "evidence_ledger": [],
                                },
                                "ad_strategy": {"claims": []},
                                "user_insight": {"claims": []},
                                "macro_context": {"claims": []},
                                "quality_audit": {"trust_score": 80, "verdict": "pass"},
                                "final_note": {"markdown_content": "# 旧格式", "one_sentence_takeaway": "一句话洞察"},
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps({}, ensure_ascii=False),
                        "2026-06-07 12:00:00",
                        "2026-06-07 12:00:00",
                    ),
                )
                await db.commit()

        asyncio.run(seed())

        response = self.client.get("/api/jobs/detail01")
        self.assertEqual(response.status_code, 200)
        markdown = response.json()["analysis"]["final_note"]["markdown_content"]
        self.assertIn("## 04｜素材解构", markdown)
        self.assertIn("## 05｜广告策略分析", markdown)
        self.assertIn("## 06｜用户洞察", markdown)
        self.assertIn("## 07｜宏观背景", markdown)
        self.assertIn("## 08｜对我的启发", markdown)


if __name__ == "__main__":
    unittest.main()
