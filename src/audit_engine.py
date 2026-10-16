import csv
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_ROOT / "data" / "financial_cases.json"
OUTPUT_DIR = PROJECT_ROOT / "output"


def calculate_expected(case):
    """Recalculate a financial metric using its supplied inputs."""
    metric = case["analysis_type"]
    inputs = case["inputs"]

    if metric == "Revenue Growth":
        prior = inputs["prior_revenue"]
        if prior == 0:
            raise ValueError("Prior revenue cannot be zero.")
        return (inputs["current_revenue"] - prior) / prior * 100

    if metric == "Gross Profit Margin":
        revenue = inputs["revenue"]
        if revenue == 0:
            raise ValueError("Revenue cannot be zero.")
        return (
            (revenue - inputs["cost_of_goods_sold"]) / revenue * 100
        )

    if metric == "Current Ratio":
        liabilities = inputs["current_liabilities"]
        if liabilities == 0:
            raise ValueError("Current liabilities cannot be zero.")
        return inputs["current_assets"] / liabilities

    if metric == "Debt-to-Equity Ratio":
        equity = inputs["shareholders_equity"]
        if equity == 0:
            raise ValueError("Shareholders' equity cannot be zero.")
        return inputs["interest_bearing_debt"] / equity

    if metric == "Price-to-Earnings Ratio":
        eps = inputs["earnings_per_share"]
        if eps == 0:
            raise ValueError("Earnings per share cannot be zero.")
        return inputs["share_price"] / eps

    if metric == "Operating Margin":
        revenue = inputs["revenue"]
        if revenue == 0:
            raise ValueError("Revenue cannot be zero.")
        return inputs["operating_income"] / revenue * 100

    if metric == "Revenue Forecast":
        growth = inputs["growth_rate_percent"]
        return inputs["base_revenue"] * (1 + growth / 100)

    if metric == "Enterprise Value":
        return inputs["ebitda"] * inputs["ev_ebitda_multiple"]

    raise ValueError(f"Unsupported analysis type: {metric}")


def audit_case(case, tolerance=0.01):
    """Compare an AI-claimed figure with the independently calculated value."""
    claimed = case["ai_claim"]

    try:
        expected = calculate_expected(case)
        difference = claimed - expected
        passed = abs(difference) <= tolerance

        return {
            "case_id": case["case_id"],
            "analysis_type": case["analysis_type"],
            "claimed_value": claimed,
            "recalculated_value": round(expected, 6),
            "difference_claim_minus_expected": round(difference, 6),
            "unit": case["unit"],
            "status": "PASS" if passed else "FAIL",
            "finding": (
                "Claim matches recalculation within tolerance."
                if passed
                else "Claim differs from independent recalculation."
            ),
        }
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        return {
            "case_id": case.get("case_id", "UNKNOWN"),
            "analysis_type": case.get("analysis_type", "UNKNOWN"),
            "claimed_value": claimed,
            "recalculated_value": None,
            "difference_claim_minus_expected": None,
            "unit": case.get("unit", "unknown"),
            "status": "REVIEW",
            "finding": f"Could not safely verify case: {error}",
        }


def run_audit():
    """Load the cases and save audit results as JSON and CSV."""
    with DATA_FILE.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    results = [audit_case(case) for case in dataset["cases"]]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    json_path = OUTPUT_DIR / "audit_results.json"
    csv_path = OUTPUT_DIR / "audit_results.csv"

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(results, file, indent=2)

    fieldnames = list(results[0].keys()) if results else []
    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if fieldnames:
            writer.writeheader()
            writer.writerows(results)

    passed = sum(result["status"] == "PASS" for result in results)
    failed = sum(result["status"] == "FAIL" for result in results)
    review = sum(result["status"] == "REVIEW" for result in results)

    print(f"Cases audited: {len(results)}")
    print(f"PASS: {passed}")
    print(f"FAIL: {failed}")
    print(f"REVIEW: {review}")
    print(f"JSON results: {json_path}")
    print(f"CSV results: {csv_path}")


if __name__ == "__main__":
    run_audit()