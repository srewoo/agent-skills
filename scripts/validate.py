#!/usr/bin/env python3
"""Lint every SKILL.md against the portable Agent Skills contract. Exit 1 on any error.

Usage: python3 scripts/validate.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
# Harness-specific tool names that break portability across agents.
HARNESS_WORDS = re.compile(r"\b(ToolSearch|TodoWrite|AskUserQuestion|NotebookEdit|the (Bash|Edit|Write|Read|Grep|Glob|Agent) tool)\b")
MAX_LINES = 400


def frontmatter(text: str):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    fields = {}
    for line in m.group(1).splitlines():
        k, sep, v = line.partition(":")
        if sep and not line.startswith(" "):
            fields[k.strip()] = v.strip().strip('"').strip("'")
    return fields


def check_skill(path: Path) -> list:
    errs, text = [], path.read_text()
    folder = path.parent.name
    fm = frontmatter(text)
    if fm is None:
        return [f"{path}: missing YAML frontmatter"]
    if set(fm) - {"name", "description"}:
        errs.append(f"{path}: extra frontmatter keys {sorted(set(fm) - {'name', 'description'})} hurt portability")
    name, desc = fm.get("name", ""), fm.get("description", "")
    if name != folder:
        errs.append(f"{path}: name '{name}' != folder '{folder}'")
    if not NAME_RE.match(name) or len(name) > 64:
        errs.append(f"{path}: invalid name '{name}'")
    if not desc.startswith("Use when"):
        errs.append(f"{path}: description must start with 'Use when'")
    if len(desc) > 1024:
        errs.append(f"{path}: description {len(desc)} chars > 1024")
    lines = text.count("\n")
    if lines > MAX_LINES:
        errs.append(f"{path}: {lines} lines > {MAX_LINES}; move reference material to references/")
    for m in HARNESS_WORDS.finditer(text):
        errs.append(f"{path}: harness-specific wording '{m.group(0)}'")
    for link in re.findall(r"\]\(((?:references|scripts)/[^)#]+)\)", text):
        if not (path.parent / link).exists():
            errs.append(f"{path}: broken link {link}")
    return errs


def main() -> int:
    errs, skills = [], sorted(ROOT.glob("plugins/*/skills/*/SKILL.md"))
    for p in skills:
        errs += check_skill(p)
    for m in [ROOT / ".claude-plugin/marketplace.json", ROOT / ".agents/plugins/marketplace.json",
              *ROOT.glob("plugins/*/.claude-plugin/plugin.json"), *ROOT.glob("plugins/*/.codex-plugin/plugin.json")]:
        try:
            json.loads(m.read_text())
        except (OSError, ValueError) as e:
            errs.append(f"{m}: {e}")
    for err in errs:
        print("ERROR", err)
    print(f"{len(skills)} skills checked, {len(errs)} errors")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
