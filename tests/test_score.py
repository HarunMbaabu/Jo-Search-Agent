import unittest

from helpers import FAKE_PROFILE
import score
from common import load_config


class TestScore(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config()

    def test_weights(self):
        w = self.cfg["ranking_weights"]
        self.assertEqual(w, {"technical_skills": 0.35, "experience": 0.25, "projects": 0.15,
                             "education": 0.10, "preferred_qualifications": 0.10,
                             "location_eligibility": 0.05})

    def test_weighted_score(self):
        comps = dict.fromkeys(score.COMPONENTS, 100)
        self.assertEqual(score.weighted_score(comps, self.cfg["ranking_weights"]), 100.0)
        comps["technical_skills"] = 0
        self.assertEqual(score.weighted_score(comps, self.cfg["ranking_weights"]), 65.0)

    def test_rejects_out_of_range(self):
        comps = dict.fromkeys(score.COMPONENTS, 100)
        comps["projects"] = 120
        with self.assertRaises(ValueError):
            score.weighted_score(comps, self.cfg["ranking_weights"])

    def test_skill_overlap_aliases(self):
        have = score.profile_skill_set(FAKE_PROFILE)
        pct, matched, missing = score.skill_overlap(["PySpark", "Postgres", "data build tool", "Tableau"], have)
        self.assertEqual(pct, 75.0)
        self.assertEqual(missing, ["tableau"])
        self.assertIn("kafka", have)  # tools from experience count

    def test_score_job_tier_and_cap(self):
        job = {"required_skills": ["python", "sql"], "location_tier": "ineligible",
               "components": {"experience": 100, "projects": 100, "education": 100,
                              "preferred_qualifications": 100}}
        res = score.score_job(job, FAKE_PROFILE, self.cfg)
        self.assertLessEqual(res["score"], 40)
        job["location_tier"] = "kenya"
        res = score.score_job(job, FAKE_PROFILE, self.cfg)
        self.assertEqual(res["score"], 100.0)
        self.assertEqual(res["band"], "strong")

    def test_unknown_tier(self):
        with self.assertRaises(ValueError):
            score.score_job({"location_tier": "mars", "components": dict.fromkeys(score.COMPONENTS, 50)},
                            FAKE_PROFILE, self.cfg)


if __name__ == "__main__":
    unittest.main()
