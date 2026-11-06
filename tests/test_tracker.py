import contextlib
import io
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from helpers import IsolatedHome
import tracker


def run(*argv) -> str:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        tracker.main(list(argv))
    return buf.getvalue()


def add(home: Path, job: dict) -> dict:
    p = home / "job.json"
    p.write_text(json.dumps(job))
    return json.loads(run("add", str(p)))[0]


JOB = {"title": "Data Engineer", "company": "Example Co", "location": "Nairobi",
       "apply_url": "https://www.example.com/careers/123/?utm_source=x&ref=abc", "source": "test"}


class TestTracker(unittest.TestCase):
    def setUp(self):
        self.ctx = IsolatedHome()
        self.home = self.ctx.__enter__()
        run("init")

    def tearDown(self):
        self.ctx.__exit__(None, None, None)

    def test_db_private(self):
        mode = stat.S_IMODE(os.stat(self.home / "tracker.db").st_mode)
        self.assertEqual(mode, 0o600)

    def test_canonical_url(self):
        self.assertEqual(tracker.canonical_url("http://WWW.Example.com/careers/123/?utm_source=x&gh_src=y&id=7"),
                         "https://example.com/careers/123?id=7")

    def test_dedupe_by_url_and_key(self):
        first = add(self.home, JOB)
        self.assertTrue(first["created"])
        again = add(self.home, {**JOB, "apply_url": "https://example.com/careers/123"})
        self.assertFalse(again["created"])
        same_key = add(self.home, {**JOB, "apply_url": "https://other.ats/job/9", "title": "Data  Engineer"})
        self.assertFalse(same_key["created"])
        other_loc = add(self.home, {**JOB, "apply_url": "https://other.ats/job/10", "location": "Mombasa"})
        self.assertTrue(other_loc["created"])  # distinct vacancy allowed, but flagged as similar
        chk = json.loads(run("check", "--company", "Example Co", "--title", "Data Engineer", "--location", "Kisumu"))
        self.assertFalse(chk["duplicate"])
        self.assertTrue(chk["similar"])

    def test_illegal_transitions(self):
        jid = add(self.home, JOB)["id"]
        with self.assertRaises(SystemExit):
            run("set-status", str(jid), "submitted")
        with self.assertRaises(SystemExit):
            run("set-status", str(jid), "ready_for_review")  # must go via shortlisted/drafted

    def _ready(self) -> int:
        jid = add(self.home, JOB)["id"]
        run("set-status", str(jid), "shortlisted")
        run("set-status", str(jid), "drafted")
        run("set-status", str(jid), "ready_for_review")
        return jid

    def test_approval_gate(self):
        jid = self._ready()
        with self.assertRaises(SystemExit) as cm:
            run("approve", str(jid), "--user-statement", "yes")
        self.assertIn("link not verified", str(cm.exception))
        run("verify-link", str(jid), "--ok")
        with self.assertRaises(SystemExit) as cm:
            run("approve", str(jid), "--user-statement", "yes")
        self.assertIn("claim-verified", str(cm.exception))
        doc = self.home / "cv.docx"; doc.write_text("x")
        run("attach-docs", str(jid), "--cv", str(doc), "--claims-verified")
        with self.assertRaises(SystemExit):
            run("mark-submitted", str(jid))  # not approved yet
        run("approve", str(jid), "--user-statement", "Yes, submit this one")
        run("mark-submitted", str(jid), "--note", "ok")
        with self.assertRaises(SystemExit):
            run("mark-submitted", str(jid))  # never twice
        shown = json.loads(run("show", str(jid)))
        self.assertEqual(shown["job"]["status"], "submitted")
        self.assertEqual(shown["application"]["approval_statement"], "Yes, submit this one")
        self.assertEqual([h["to_status"] for h in shown["history"] if h["to_status"]][-2:], ["approved", "submitted"])

    def test_cannot_approve_via_set_status(self):
        jid = self._ready()
        with self.assertRaises(SystemExit):
            run("set-status", str(jid), "approved")

    def test_stats_and_export(self):
        add(self.home, JOB)
        stats = json.loads(run("stats"))
        self.assertEqual(stats["total"], 1)
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "x.csv"
            run("export-csv", str(out))
            self.assertIn("Example Co", out.read_text())


if __name__ == "__main__":
    unittest.main()
