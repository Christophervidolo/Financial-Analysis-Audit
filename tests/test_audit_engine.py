import sys
import unittest
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent / "src")
)

from audit_engine import audit_case, calculate_expected


class TestFinancialAudit(unittest.TestCase):

    def test_revenue_growth(self):
        case = {
            "case_id": "TEST-01",
            "analysis_type": "Revenue Growth",
            "inputs": {
                "prior_revenue": 100,
                "current_revenue": 115,
            },
            "ai_claim": 15,
            "unit": "percent",
        }
        self.assertAlmostEqual(calculate_expected(case), 15)
        self.assertEqual(audit_case(case)["status"], "PASS")

    def test_wrong_claim_is_flagged(self):
        case = {
            "case_id": "TEST-02",
            "analysis_type": "Current Ratio",
            "inputs": {
                "current_assets": 300,
                "current_liabilities": 150,
            },
            "ai_claim": 1,
            "unit": "multiple",
        }
        result = audit_case(case)
        self.assertAlmostEqual(result["recalculated_value"], 2)
        self.assertEqual(result["status"], "FAIL")

    def test_zero_denominator_is_reviewed(self):
        case = {
            "case_id": "TEST-03",
            "analysis_type": "Current Ratio",
            "inputs": {
                "current_assets": 300,
                "current_liabilities": 0,
            },
            "ai_claim": 1,
            "unit": "multiple",
        }
        self.assertEqual(audit_case(case)["status"], "REVIEW")

    def test_enterprise_value(self):
        case = {
            "case_id": "TEST-04",
            "analysis_type": "Enterprise Value",
            "inputs": {
                "ebitda": 250000,
                "ev_ebitda_multiple": 8,
            },
            "ai_claim": 2000000,
            "unit": "currency",
        }
        self.assertEqual(calculate_expected(case), 2000000)
        self.assertEqual(audit_case(case)["status"], "PASS")


if __name__ == "__main__":
    unittest.main()