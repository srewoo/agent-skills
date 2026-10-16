"""Run: python3 test_validate.py  (stdlib unittest, no install needed)."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import check_skill, frontmatter  # noqa: E402

VALID = """---
name: my-skill
description: Use when you need a fixture.
---
# My skill

See [the guide](references/guide.md) and run [the script](scripts/run.py#usage).
"""


class CheckSkill(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name) / "my-skill"
        (self.dir / "references").mkdir(parents=True)
        (self.dir / "scripts").mkdir()
        (self.dir / "references" / "guide.md").write_text("x")
        (self.dir / "scripts" / "run.py").write_text("x")

    def tearDown(self):
        self.tmp.cleanup()

    def errors(self, text, folder=None):
        d = self.dir if folder is None else self.dir.parent / folder
        d.mkdir(exist_ok=True)
        p = d / "SKILL.md"
        p.write_text(text)
        return check_skill(p)

    def assertOneError(self, text, fragment, folder=None):
        errs = self.errors(text, folder)
        self.assertEqual(len(errs), 1, errs)
        self.assertIn(fragment, errs[0])

    def test_valid_skill_passes(self):
        self.assertEqual(self.errors(VALID), [])

    def test_quoted_values_accepted(self):
        text = VALID.replace("name: my-skill", 'name: "my-skill"')
        self.assertEqual(self.errors(text), [])

    def test_wrong_name(self):
        self.assertOneError(VALID.replace("name: my-skill", "name: other-skill"),
                            "name 'other-skill' != folder 'my-skill'")

    def test_invalid_name_format(self):
        text = VALID.replace("name: my-skill", "name: My_Skill").split("See [")[0]  # no links in this folder
        errs = self.errors(text, folder="My_Skill")
        self.assertEqual(len(errs), 1, errs)
        self.assertIn("invalid name 'My_Skill'", errs[0])

    def test_missing_use_when(self):
        self.assertOneError(VALID.replace("Use when you", "Helps you"), "must start with 'Use when'")

    def test_description_too_long(self):
        self.assertOneError(VALID.replace("a fixture.", "x" * 1100), "> 1024")

    def test_extra_frontmatter_key(self):
        self.assertOneError(VALID.replace("---\n#", "license: MIT\n---\n#"), "extra frontmatter keys ['license']")

    def test_harness_words(self):
        errs = self.errors(VALID + "\nUse TodoWrite, then call the Bash tool.\n")
        self.assertEqual(len(errs), 2, errs)
        self.assertIn("'TodoWrite'", errs[0])
        self.assertIn("'the Bash tool'", errs[1])

    def test_broken_references_link(self):
        self.assertOneError(VALID + "\n[missing](references/nope.md)\n", "broken link references/nope.md")

    def test_too_many_lines(self):
        self.assertOneError(VALID + "line\n" * 400, "lines > 400")

    def test_missing_frontmatter(self):
        self.assertOneError("# no frontmatter\n", "missing YAML frontmatter")

    def test_frontmatter_ignores_indented_lines(self):
        fm = frontmatter("---\nname: a\ndescription: Use when\n  nested: x\n---\n")
        self.assertEqual(fm, {"name": "a", "description": "Use when"})


if __name__ == "__main__":
    unittest.main()
