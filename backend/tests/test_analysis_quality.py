import unittest

from app.analysis_quality import (
    apply_quality_gate,
    normalize_audit,
    normalize_evidence_ledger,
    publication_claims,
)


class EvidenceNormalizationTests(unittest.TestCase):
    def test_assigns_stable_ids_and_drops_empty_observations(self):
        ledger = normalize_evidence_ledger(
            {
                "evidence_ledger": [
                    {"timestamp": "00:03", "observation": "画面出现30瓶饮料", "modality": "visual"},
                    {"timestamp": "", "observation": "", "modality": "audio"},
                    {"id": "custom", "timestamp": "00:08", "observation": "口播提到好喝不贵"},
                ]
            }
        )

        self.assertEqual([item["id"] for item in ledger], ["E001", "E002"])
        self.assertEqual(ledger[0]["timestamp"], "00:03")
        self.assertEqual(ledger[1]["modality"], "unknown")

    def test_unsupported_observed_claim_is_downgraded(self):
        evidence = [{"id": "E001", "observation": "出现产品", "timestamp": "00:01"}]
        section = {
            "claims": [
                {
                    "claim": "销量增长300%",
                    "claim_type": "observed",
                    "confidence": "high",
                    "evidence_ids": ["E999"],
                },
                {
                    "claim": "用价格反差吸引注意",
                    "claim_type": "inferred",
                    "confidence": "medium",
                    "evidence_ids": ["E001"],
                },
            ]
        }

        gated = apply_quality_gate(section, evidence)

        self.assertEqual(gated["claims"][0]["claim_type"], "hypothesis")
        self.assertEqual(gated["claims"][0]["confidence"], "low")
        self.assertEqual(gated["claims"][0]["support_status"], "unsupported")
        self.assertEqual(gated["claims"][1]["support_status"], "partially_supported")


class AuditNormalizationTests(unittest.TestCase):
    def test_local_gate_can_force_review_even_when_model_says_pass(self):
        audit = normalize_audit(
            {
                "trust_score": 96,
                "verdict": "pass",
                "unsupported_claims": [],
                "contradictions": [],
                "limitations": [],
            },
            claims=[
                {
                    "claim_id": "C001",
                    "claim": "未经证实的效果",
                    "claim_type": "hypothesis",
                    "support_status": "unsupported",
                    "evidence_ids": [],
                }
            ],
        )

        self.assertEqual(audit["verdict"], "review")
        self.assertLessEqual(audit["trust_score"], 69)
        self.assertIn("未经证实的效果", audit["unsupported_claims"])
        self.assertIn("C001", audit["unsupported_claim_ids"])

    def test_publication_context_excludes_model_rejected_claim_ids(self):
        claims = [
            {"claim_id": "C001", "claim": "可保留推断", "support_status": "partially_supported"},
            {"claim_id": "C002", "claim": "被否决推断", "support_status": "partially_supported"},
        ]
        audit = {
            "approved_claim_ids": ["C001"],
            "unsupported_claim_ids": ["C002"],
        }

        result = publication_claims(claims, audit)

        self.assertEqual([item["claim_id"] for item in result], ["C001"])

    def test_trust_score_is_calibrated_when_model_score_conflicts_with_approvals(self):
        claims = [
            {
                "claim_id": f"C{index:03d}",
                "claim": f"推断{index}",
                "support_status": "partially_supported",
            }
            for index in range(1, 6)
        ]
        audit = normalize_audit(
            {
                "trust_score": 0,
                "verdict": "review",
                "approved_claim_ids": ["C001", "C002", "C003", "C004"],
                "unsupported_claim_ids": ["C005"],
                "unsupported_claims": ["推断5措辞越界"],
                "contradictions": [],
                "limitations": ["缺少投放数据"],
            },
            claims=claims,
        )

        self.assertGreaterEqual(audit["trust_score"], 50)
        self.assertEqual(audit["model_trust_score"], 0)


if __name__ == "__main__":
    unittest.main()
