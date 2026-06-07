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


class ComparisonApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "compare.db"
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

    def _seed(self, ad_id: str, brand: str, status="completed"):
        analysis = json.dumps({"scoring": {"scoring": {"overall_score": 65, "tier": "B级"}}})
        async def _do():
            async with aiosqlite.connect(str(self.db_path)) as db:
                await db.execute(
                    "INSERT INTO ads (id, brand_name, product_name, industry, platform, status, analysis_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (ad_id, brand, "产品X", "美妆", "抖音", status, analysis),
                )
                await db.commit()
        asyncio.run(_do())

    def test_same_ad_rejected(self):
        resp = self.client.post("/api/compare", json={"ad_id_a": "same", "ad_id_b": "same"})
        self.assertEqual(resp.status_code, 400)

    def test_missing_ad_returns_404(self):
        resp = self.client.post("/api/compare", json={"ad_id_a": "no-exist-1", "ad_id_b": "no-exist-2"})
        self.assertEqual(resp.status_code, 404)

    def test_unanalyzed_ad_returns_400(self):
        self._seed("p1", "品牌A", "pending")
        self._seed("p2", "品牌B", "pending")
        resp = self.client.post("/api/compare", json={"ad_id_a": "p1", "ad_id_b": "p2"})
        self.assertEqual(resp.status_code, 400)

    @patch("app.comparison_engine.is_configured", return_value=False)
    def test_mock_comparison_returns_structure(self, mock_cfg):
        self._seed("c1", "品牌A")
        self._seed("c2", "品牌B")
        resp = self.client.post("/api/compare", json={"ad_id_a": "c1", "ad_id_b": "c2"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("predicted_winner", data)
        self.assertIn("ad_a", data)
        self.assertIn("ad_b", data)
        self.assertEqual(data["ad_a"]["overall_score"], 65)
        self.assertEqual(data["ad_b"]["overall_score"], 65)


class ComparisonEngineTests(unittest.IsolatedAsyncioTestCase):
    async def test_mock_comparison_structure(self):
        from app.comparison_engine import _mock_comparison
        result = _mock_comparison({}, {})
        self.assertEqual(result["predicted_winner"], "tie")
        self.assertIsInstance(result["key_differences"], list)

    @patch("app.comparison_engine.is_configured", return_value=True)
    @patch("app.comparison_engine.chat_completion")
    async def test_llm_comparison_mocked(self, mock_chat, mock_cfg):
        mock_chat.return_value = {
            "predicted_winner": "A", "confidence": "high",
            "key_differences": ["钩子差异"], "analysis_markdown": "分析",
            "ad_a_strengths": ["钩子强"], "ad_a_weaknesses": [],
            "ad_b_strengths": ["转化好"], "ad_b_weaknesses": ["开头弱"],
            "hook_comparison": "A好", "audience_comparison": "A准", "trust_comparison": "B强",
        }
        from app.comparison_engine import run_comparison

        ad_a = {"brand_name": "A", "product_name": "X", "industry": "食品", "platform": "抖音", "analysis_json": json.dumps({"scoring": {"overall_score": 70}})}
        ad_b = {"brand_name": "B", "product_name": "Y", "industry": "食品", "platform": "抖音", "analysis_json": json.dumps({"scoring": {"overall_score": 55}})}

        result = await run_comparison(ad_a, ad_b)
        self.assertEqual(result["predicted_winner"], "A")
        self.assertEqual(result["confidence"], "high")


if __name__ == "__main__":
    unittest.main()
