#!/usr/bin/env python3
"""Generate every plugin/marketplace manifest from TOOLKITS so Claude Code and Codex never drift.

Usage: python3 scripts/build_manifests.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = "1.0.0"
OWNER = {"name": "Sharaj Rewoo", "url": "https://github.com/srewoo"}
REPO = "https://github.com/srewoo/agent-skills"
MARKETPLACE = "agent-skills"

TOOLKITS = {
    "dev-toolkit": ("Developer Toolkit", "Coding",
                    "Major-version upgrades, splitting large PRs, and safely deleting dead code.",
                    ["upgrade", "migration", "pull-request", "refactor", "dead-code"]),
    "qa-toolkit": ("QA Toolkit", "Coding",
                   "Hunting flaky tests, turning bug reports into failing tests, and finding untested changes.",
                   ["testing", "flaky-tests", "qa", "coverage", "bug-repro"]),
    "ai-eng-toolkit": ("AI Engineering Toolkit", "Coding",
                       "Evals, prompt regression testing, RAG debugging, and LLM cost reduction.",
                       ["llm", "evals", "rag", "prompts", "cost"]),
    "seo-toolkit": ("SEO Toolkit", "Productivity",
                    "Technical SEO audits, keyword clustering, and competitor content-gap analysis.",
                    ["seo", "keywords", "content-strategy", "audit"]),
    "hr-toolkit": ("HR Toolkit", "Productivity",
                   "Inclusive JDs, structured interviews, fair resume screening, policies, onboarding, and feedback.",
                   ["hr", "hiring", "recruiting", "onboarding", "feedback"]),
    "content-toolkit": ("Content Toolkit", "Productivity",
                        "Removing AI-sounding prose, matching a brand voice, and repurposing content across channels.",
                        ["writing", "content", "brand-voice", "social-media"]),
    "support-toolkit": ("Support Toolkit", "Productivity",
                        "Triaging helpdesk tickets and drafting replies, merges and escalations for a human to send.",
                        ["support", "helpdesk", "triage", "customer-success"]),
}


def write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def skills_of(toolkit: str) -> list:
    return sorted(p.parent.name for p in (ROOT / "plugins" / toolkit / "skills").glob("*/SKILL.md"))


def main() -> None:
    claude_entries, codex_entries = [], []
    for name, (display, category, desc, keywords) in TOOLKITS.items():
        base = ROOT / "plugins" / name
        skills = skills_of(name)
        write(base / ".claude-plugin" / "plugin.json", {
            "name": name, "version": VERSION, "description": desc,
            "author": OWNER, "homepage": REPO, "repository": REPO,
            "license": "MIT", "keywords": keywords,
        })
        write(base / ".codex-plugin" / "plugin.json", {
            "name": name, "version": VERSION, "description": desc,
            "author": OWNER, "homepage": REPO, "repository": REPO,
            "license": "MIT", "keywords": keywords, "skills": "./skills/",
            "interface": {
                "displayName": display, "shortDescription": desc,
                "developerName": OWNER["name"], "category": category,
                "capabilities": ["Read", "Write"],
                "defaultPrompt": [f"Use ${s}" for s in skills[:3]],
            },
        })
        claude_entries.append({"name": name, "source": f"./plugins/{name}",
                               "description": desc, "version": VERSION, "keywords": keywords})
        codex_entries.append({"name": name,
                              "source": {"source": "local", "path": f"./plugins/{name}"},
                              "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                              "category": category})

    write(ROOT / ".claude-plugin" / "marketplace.json", {
        "name": MARKETPLACE, "owner": OWNER,
        "metadata": {"description": "Portable agent skills for developers, QA, AI engineers, SEO, HR, content and support teams.",
                     "version": VERSION},
        "plugins": claude_entries,
    })
    write(ROOT / ".agents" / "plugins" / "marketplace.json", {
        "name": MARKETPLACE, "interface": {"displayName": "Agent Skills"},
        "plugins": codex_entries,
    })
    print(f"wrote manifests for {len(TOOLKITS)} toolkits")


if __name__ == "__main__":
    main()
