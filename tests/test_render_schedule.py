import contextlib
import io
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import SKILL_DIR, IsolatedHome
import render_docs
import schedule

MD = """# Test Candidate
candidate@example.com · Nairobi, Kenya

## Skills
- **Languages:** Python, SQL

## Experience
### Data Engineer | Acme Data | Jan 2022 – Present
- Built pipelines with Airflow.
"""


@unittest.skipUnless(sys.platform == "darwin" and shutil.which("textutil"), "macOS textutil required")
class TestRender(unittest.TestCase):
    def test_docx_and_txt(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "cv.md"
            src.write_text(MD)
            out = Path(d) / "out"
            produced = render_docs.render(src, out, "Test_CV", {"docx", "txt"})
            self.assertEqual({p.suffix for p in produced}, {".docx", ".txt"})
            for p in produced:
                self.assertEqual(stat.S_IMODE(os.stat(p).st_mode), 0o600)
            text = subprocess.run(["textutil", "-convert", "txt", "-stdout", str(out / "Test_CV.docx")],
                                  capture_output=True, text=True, check=True).stdout
            self.assertIn("Built pipelines with Airflow.", text)
            self.assertIn("EXPERIENCE".lower(), text.lower())
            self.assertFalse((out / "Test_CV.html").exists())

    def test_html_has_no_tables_or_images(self):
        page = render_docs.md_to_html(MD, "x")
        self.assertNotIn("<table", page)
        self.assertNotIn("<img", page)
        self.assertIn("<li>Built pipelines with Airflow.</li>", page)


class TestSchedule(unittest.TestCase):
    def test_times_nairobi(self):
        times = schedule.local_times(["08:00", "11:00", "14:00", "17:00", "20:00"], "Africa/Nairobi")
        self.assertEqual(len(times), 5)
        self.assertTrue(all(t["Minute"] == 0 for t in times))

    def test_install_requires_approval(self):
        with IsolatedHome():
            res = subprocess.run([sys.executable, str(SKILL_DIR / "scripts" / "schedule.py"), "install"],
                                 capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("explicit user approval", res.stderr)

    def test_preview_changes_nothing(self):
        existed = schedule.PLIST.exists()
        with IsolatedHome():
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                sys.argv = ["schedule.py", "preview"]
                schedule.main()
        self.assertIn("Nothing has been installed", buf.getvalue())
        self.assertEqual(schedule.PLIST.exists(), existed)


if __name__ == "__main__":
    unittest.main()
