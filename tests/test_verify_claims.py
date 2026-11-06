import unittest

from helpers import FAKE_PROFILE
import verify_claims

CLEAN = """# Test Candidate
candidate@example.com | +000000000 | Nairobi, Kenya

## Summary
Data Engineer with 4 years of experience in Python, SQL, Airflow, dbt, Spark and Snowflake on AWS.

## Experience
### Data Engineer | Acme Data | Nairobi, Kenya | Jan 2022 – Present
- Cut processing time by 30% by moving ETL to ELT with dbt; streamed events with Kafka.
- Built PySpark jobs and PostgreSQL models.

## Education
### BSc Computer Science | Example University | 2016 – 2020
"""


class TestVerifyClaims(unittest.TestCase):
    def test_clean_document(self):
        res = verify_claims.check(CLEAN, FAKE_PROFILE)
        self.assertTrue(res["clean"], res)

    def test_flags_fabricated_tool(self):
        res = verify_claims.check(CLEAN + "\n- Built dashboards in Tableau and Kubernetes.\n", FAKE_PROFILE)
        self.assertIn("tableau", res["issues"]["unverified_terms"])  # flags text must not count as evidence
        self.assertIn("kubernetes", res["issues"]["unverified_terms"])

    def test_flags_metric_years_degree_employer(self):
        doc = CLEAN + "\n10+ years experience. Improved revenue by 45%. MSc Data Science.\n" \
                      "### Lead Engineer | Globex Corp | 2019 – 2021\n"
        issues = verify_claims.check(doc, FAKE_PROFILE)["issues"]
        self.assertIn("45%", issues["unverified_metrics"])
        self.assertTrue(any(c.startswith("10+ years") for c in issues["years_claims"]))
        self.assertIn("msc", issues["unverified_terms"])
        self.assertIn("globex corp", issues["unknown_employers"])


if __name__ == "__main__":
    unittest.main()
