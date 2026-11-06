import json
import re
import unittest

from helpers import SKILL_DIR


def frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, "SKILL.md must start with YAML frontmatter delimited by ---"
    out = {}
    for line in m.group(1).splitlines():
        if not line.strip():
            continue
        key, sep, val = line.partition(":")
        assert sep, f"bad frontmatter line: {line!r}"
        out[key.strip()] = val.strip().strip('"')
    return out


class TestSkillMd(unittest.TestCase):
    def setUp(self):
        self.text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.fm = frontmatter(self.text)

    def test_frontmatter(self):
        self.assertEqual(self.fm["name"], "job_agents")
        self.assertEqual(self.fm["disable-model-invocation"], "true")
        self.assertGreater(len(self.fm["description"]), 80)
        self.assertLessEqual(len(self.fm["description"]), 1024)

    def test_yaml_parses_if_pyyaml_available(self):
        try:
            import yaml  # type: ignore
        except ImportError:
            self.skipTest("PyYAML not installed")
        fm = yaml.safe_load(self.text.split("---")[1])
        self.assertIs(fm["disable-model-invocation"], True)

    def test_required_sections(self):
        for section in ("Role", "Objective", "Inputs", "Workflow", "Outputs", "Constraints", "Validation"):
            self.assertRegex(self.text, rf"(?m)^## {section}\s*$", f"missing section {section}")

    def test_referenced_files_exist(self):
        for rel in re.findall(r"`((?:references|scripts|config)/[\w./-]+)`", self.text):
            self.assertTrue((SKILL_DIR / rel).exists(), f"SKILL.md references missing file {rel}")
        for script in re.findall(r"scripts/(\w+\.py)", self.text):
            self.assertTrue((SKILL_DIR / "scripts" / script).exists(), script)

    def test_config_valid(self):
        cfg = json.loads((SKILL_DIR / "config" / "search_config.json").read_text())
        self.assertAlmostEqual(sum(cfg["ranking_weights"].values()), 1.0)
        self.assertEqual(cfg["schedule"]["times_local"], ["08:00", "11:00", "14:00", "17:00", "20:00"])
        self.assertFalse(cfg["schedule"]["enabled"])
        self.assertEqual(cfg["timezone"], "Africa/Nairobi")


if __name__ == "__main__":
    unittest.main()
