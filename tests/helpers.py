"""Test helpers: isolated data dir + a SYNTHETIC profile (no real CV data in source)."""
import json
import os
import sys
import tempfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))

FAKE_PROFILE = {
    "source_cv": "/tmp/fake.pdf",
    "verified_at": "2026-01-01",
    "name": "Test Candidate",
    "headline": "Data Engineer",
    "contact": {"email": "candidate@example.com", "phone": "+000000000"},
    "location": {"city": "Nairobi", "country": "Kenya"},
    "links": {},
    "max_years_claim": 4,
    "skills": {
        "languages": ["Python", "SQL"],
        "data_engineering": ["Apache Airflow", "dbt", "Apache Spark"],
        "cloud_and_storage": ["AWS", "Snowflake", "PostgreSQL"],
        "analytics_and_bi": ["Data Visualization and Analysis"],
        "ml_ai": ["XGBoost"],
    },
    "experience": [{
        "title": "Data Engineer", "employer": "Acme Data", "location": "Nairobi, Kenya",
        "work_mode": "Onsite", "start": "2022-01", "end": "Present",
        "highlights": ["Cut processing time by 30% by moving ETL to ELT with dbt."],
        "tools": ["Kafka"],
    }],
    "education": [{"institution": "Example University", "qualification": "BSc Computer Science",
                   "start": "2016", "end": "2020"}],
    "projects": [],
    "certifications": [],
    "flags": ["No Tableau or Power BI listed."],
}


class IsolatedHome:
    """Context manager pointing JOB_AGENTS_HOME at a temp dir with the fake profile."""

    def __enter__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = os.environ.get("JOB_AGENTS_HOME")
        os.environ["JOB_AGENTS_HOME"] = self.tmp.name
        Path(self.tmp.name, "profile.json").write_text(json.dumps(FAKE_PROFILE))
        return Path(self.tmp.name)

    def __exit__(self, *exc):
        if self.old is None:
            os.environ.pop("JOB_AGENTS_HOME", None)
        else:
            os.environ["JOB_AGENTS_HOME"] = self.old
        self.tmp.cleanup()
