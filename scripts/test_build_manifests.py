"""Run: python3 test_build_manifests.py  (stdlib unittest, no install needed).

Builds into a temp copy of the repo layout by monkeypatching ROOT; never rewrites the real manifests.
"""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_manifests as bm  # noqa: E402

REAL_ROOT = bm.ROOT
MANIFESTS = [".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json"] + [
    f"plugins/{t}/{d}/plugin.json" for t in bm.TOOLKITS for d in (".claude-plugin", ".codex-plugin")]


class BuildManifests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        bm.ROOT = self.root

    def tearDown(self):
        bm.ROOT = REAL_ROOT
        self.tmp.cleanup()

    def skill(self, toolkit, name):
        p = self.root / "plugins" / toolkit / "skills" / name / "SKILL.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("---\nname: x\n---\n")

    def build(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            bm.main()
        return out.getvalue()

    def read(self, rel):
        return json.loads((self.root / rel).read_text())

    def test_writes_every_manifest_into_root(self):
        self.assertIn(f"wrote manifests for {len(bm.TOOLKITS)} toolkits", self.build())
        for rel in MANIFESTS:
            self.assertTrue((self.root / rel).is_file(), rel)

    def test_marketplaces_list_every_toolkit(self):
        self.build()
        claude = self.read(".claude-plugin/marketplace.json")
        codex = self.read(".agents/plugins/marketplace.json")
        self.assertEqual([p["name"] for p in claude["plugins"]], list(bm.TOOLKITS))
        self.assertEqual([p["source"]["path"] for p in codex["plugins"]],
                         [f"./plugins/{t}" for t in bm.TOOLKITS])
        self.assertTrue(all(p["version"] == bm.VERSION for p in claude["plugins"]))

    def test_codex_default_prompt_uses_first_three_sorted_skills(self):
        for name in ("zeta", "alpha", "mid", "beta"):
            self.skill("qa-toolkit", name)
        self.build()
        qa = self.read("plugins/qa-toolkit/.codex-plugin/plugin.json")
        self.assertEqual(qa["interface"]["defaultPrompt"], ["Use $alpha", "Use $beta", "Use $mid"])
        self.assertEqual(qa["interface"]["category"], "Coding")
        empty = self.read("plugins/hr-toolkit/.codex-plugin/plugin.json")
        self.assertEqual(empty["interface"]["defaultPrompt"], [])

    def test_claude_and_codex_plugin_share_metadata(self):
        self.build()
        for t in bm.TOOLKITS:
            c = self.read(f"plugins/{t}/.claude-plugin/plugin.json")
            x = self.read(f"plugins/{t}/.codex-plugin/plugin.json")
            for key in ("name", "version", "description", "keywords", "license"):
                self.assertEqual(c[key], x[key], (t, key))

    def test_committed_manifests_match_generator(self):
        for p in REAL_ROOT.glob("plugins/*/skills/*/SKILL.md"):
            self.skill(p.parts[-4], p.parts[-2])
        self.build()
        for rel in MANIFESTS:
            real = REAL_ROOT / rel
            if real.exists():
                self.assertEqual(self.read(rel), json.loads(real.read_text()),
                                 f"{rel} drifted; run python3 scripts/build_manifests.py")


if __name__ == "__main__":
    unittest.main()
