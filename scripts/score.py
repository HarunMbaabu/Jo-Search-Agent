#!/usr/bin/env python3
"""Rank a job against the verified profile.

Weights (from config/search_config.json):
  technical_skills 35% | experience 25% | projects 15% | education 10% |
  preferred_qualifications 10% | location_eligibility 5%

Input: a job JSON file (or '-' for stdin) shaped like:
{
  "title": "...", "company": "...",
  "required_skills": ["python", "sql", "airflow"],      # optional -> auto technical score
  "location_tier": "kenya|remote_kenya_ok|relocation_sponsored|unclear|ineligible",
  "components": {                                         # 0-100 each, judged with references/scoring_rubric.md
     "technical_skills": 80, "experience": 70, "projects": 40,
     "education": 90, "preferred_qualifications": 50, "location_eligibility": 100
  },
  "evidence": {"experience": "..."}                       # short justification per component
}

If required_skills is given, technical_skills is computed deterministically from overlap with
the verified profile's skills (aliases normalised). If location_tier is given, location_eligibility
is taken from the tier table. Ineligible jobs are capped at 40 so they never rank as strong matches.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_config, load_profile, norm  # noqa: E402

COMPONENTS = ("technical_skills", "experience", "projects", "education",
              "preferred_qualifications", "location_eligibility")

ALIASES = {
    "postgres": "postgresql", "postgre sql": "postgresql", "psql": "postgresql",
    "gcp": "google cloud", "google cloud platform": "google cloud",
    "amazon web services": "aws", "aws s3": "s3", "amazon s3": "s3", "amazon redshift": "redshift",
    "aws glue": "glue", "aws rds": "rds", "amazon dynamodb": "dynamodb",
    "big query": "bigquery", "google bigquery": "bigquery",
    "pyspark": "spark", "apache spark": "spark", "spark sql": "spark",
    "apache airflow": "airflow", "apache kafka": "kafka",
    "data build tool": "dbt", "dbt core": "dbt", "dbt cloud": "dbt",
    "microsoft azure": "azure", "azure databricks": "databricks",
    "r language": "r", "r programming": "r",
    "large language models": "llms", "llm": "llms", "natural language processing": "nlp",
    "machine learning": "ml", "scikit learn": "scikit-learn", "sklearn": "scikit-learn",
    "xgb": "xgboost", "k nearest neighbors": "knn", "k-nearest neighbors": "knn",
    "etl development": "etl", "elt": "etl", "data modelling": "data modeling",
    "infrastructure as code": "terraform", "mongo": "mongodb", "mongo db": "mongodb",
}


def canon(skill: str) -> str:
    s = norm(skill)
    return ALIASES.get(s, s)


def profile_skill_set(profile: dict) -> set[str]:
    skills: set[str] = set()
    for items in profile.get("skills", {}).values():
        skills.update(canon(i) for i in items)
    for exp in profile.get("experience", []):
        skills.update(canon(t) for t in exp.get("tools", []))
    for proj in profile.get("projects", []):
        skills.update(canon(t) for t in proj.get("tools", []))
    return skills


def skill_overlap(required: list[str], have: set[str]) -> tuple[float, list[str], list[str]]:
    req = [canon(r) for r in required if r.strip()]
    if not req:
        return 0.0, [], []
    matched = [r for r in req if r in have]
    missing = [r for r in req if r not in have]
    return round(100 * len(matched) / len(req), 1), matched, missing


def weighted_score(components: dict, weights: dict) -> float:
    total_w = sum(weights[c] for c in COMPONENTS)
    if abs(total_w - 1.0) > 1e-6:
        raise ValueError(f"weights must sum to 1.0, got {total_w}")
    for c in COMPONENTS:
        v = components.get(c)
        if v is None:
            raise ValueError(f"missing component score: {c}")
        if not 0 <= float(v) <= 100:
            raise ValueError(f"{c} must be within 0-100, got {v}")
    return round(sum(float(components[c]) * weights[c] for c in COMPONENTS), 1)


def score_job(job: dict, profile: dict | None = None, config: dict | None = None) -> dict:
    config = config or load_config()
    weights = config["ranking_weights"]
    comps = dict(job.get("components") or {})
    detail: dict = {}
    if job.get("required_skills"):
        profile = profile if profile is not None else load_profile()
        tech, matched, missing = skill_overlap(job["required_skills"], profile_skill_set(profile))
        comps["technical_skills"] = tech
        detail.update(matched_skills=matched, missing_skills=missing)
    tier = job.get("location_tier")
    if tier:
        tiers = {t["tier"]: t["eligibility_score"] for t in config["location_tiers"]}
        if tier not in tiers:
            raise ValueError(f"unknown location_tier {tier!r}; expected one of {sorted(tiers)}")
        comps["location_eligibility"] = tiers[tier]
    total = weighted_score(comps, weights)
    if tier == "ineligible":
        total = min(total, 40.0)
        detail["capped"] = "ineligible location - capped at 40"
    th = config["thresholds"]
    band = "strong" if total >= th["strong_match_score"] else "shortlist" if total >= th["shortlist_min_score"] else "low"
    return {"score": total, "band": band, "components": comps, **detail}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("job_json", help="path to job JSON, or - for stdin")
    a = ap.parse_args()
    raw = sys.stdin.read() if a.job_json == "-" else Path(a.job_json).read_text(encoding="utf-8")
    print(json.dumps(score_job(json.loads(raw)), indent=2))


if __name__ == "__main__":
    main()
