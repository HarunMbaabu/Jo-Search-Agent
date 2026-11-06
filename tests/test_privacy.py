"""Guard: no personal data in skill source. Uses the real private profile (if present) to know what
to look for, so the sensitive values themselves never appear in this file."""
import json
import re
import unittest
from pathlib import Path

from helpers import SKILL_DIR

SOURCE_SUFFIXES = {".md", ".py", ".json", ".txt", ".sh", ".plist", ".yaml", ".yml"}
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
KE_PHONE = re.compile(r"(?:\+?254|\b0)[17]\d{8}\b")
ALLOWED_EMAILS = {"candidate@example.com", "noreply@anthropic.com"}


def source_files():
    for p in SKILL_DIR.rglob("*"):
        if p.is_file() and p.suffix in SOURCE_SUFFIXES and "__pycache__" not in p.parts:
            yield p


class TestPrivacy(unittest.TestCase):
    def test_no_emails_or_kenyan_phones(self):
        for p in source_files():
            text = p.read_text(encoding="utf-8", errors="ignore")
            emails = set(EMAIL.findall(text)) - ALLOWED_EMAILS
            self.assertFalse(emails, f"email address found in {p.relative_to(SKILL_DIR)}")
            self.assertFalse(KE_PHONE.search(text), f"phone number found in {p.relative_to(SKILL_DIR)}")

    def test_real_profile_values_not_in_source(self):
        prof_path = Path.home() / ".job_agents" / "profile.json"
        if not prof_path.exists():
            self.skipTest("no private profile yet")
        prof = json.loads(prof_path.read_text())
        needles = [prof.get("name", "")] + list((prof.get("contact") or {}).values())
        needles += [e["employer"] for e in prof.get("experience", [])]
        needles += [h for e in prof.get("experience", []) for h in e.get("highlights", [])][:20]
        needles = [n for n in needles if isinstance(n, str) and len(n) >= 6]
        for p in source_files():
            text = p.read_text(encoding="utf-8", errors="ignore")
            for n in needles:
                # assertFalse (not assertNotIn) so the failure message never echoes the private value
                self.assertFalse(n in text, f"a private profile value leaked into {p.relative_to(SKILL_DIR)}")

    def test_private_dir_permissions(self):
        home = Path.home() / ".job_agents"
        if not home.exists():
            self.skipTest("no private dir yet")
        self.assertEqual(home.stat().st_mode & 0o077, 0, "~/.job_agents must be owner-only")
        for f in home.iterdir():
            if f.is_file():
                self.assertEqual(f.stat().st_mode & 0o077, 0, f"{f.name} must be owner-only")


if __name__ == "__main__":
    unittest.main()
