# Writing a skill for this marketplace

Every skill here must run unchanged in **Claude Code, OpenAI Codex, Cursor and Google Antigravity** (and, for non-code skills, in plain chat apps like claude.ai). That one constraint drives most of the rules below.

## Layout

```
plugins/<toolkit>/skills/<skill-name>/
  SKILL.md            # required
  references/*.md     # optional: heavy reference the agent loads only when needed
  scripts/*           # optional: stdlib-only helpers (Python 3.9+ or POSIX sh), tested
```

## Frontmatter

Only two fields, for portability:

```yaml
---
name: skill-name            # lowercase, hyphens, must equal the folder name
description: Use when ...   # <= 500 chars, third person
---
```

The description says **when** to load the skill: triggers, symptoms and phrases a user would type. It must never summarise the workflow, because agents follow a summarised workflow instead of reading the body.

## Body contract

Write sections in this order. Leave out any section that doesn't apply.

1. `# Title` + **Overview**: the core principle in 1-3 sentences.
2. **When to use / When not to use**: bullets. Name the neighbouring skill to use instead when there is one.
3. **Inputs**: what the agent needs. Give a sensible default for each, and ask the user only for inputs with no safe default, all in one message.
4. **Workflow**: numbered steps. Each step ends with a check that tells the agent it's done. Give real commands for each ecosystem it covers (npm/pnpm/yarn, pip/uv/poetry, Maven/Gradle, Go, …).
5. **Output**: the exact shape of the deliverable (a template or table). The user should be able to predict the output.
6. **Guardrails**: what the agent must never do, or must get confirmation for first (deleting code, pushing, sending, decisions about people).
7. **Common mistakes**: a table with two columns, *Mistake | Fix*.
8. **Example**: one short, realistic example. Leave out filler.

## Rules

- **Tool-agnostic wording.** Write "run", "read the file", "search the codebase". Never name a harness-specific tool (`Bash`, `Edit`, `Agent`, `ToolSearch`, `@file`) or a vendor slash command.
- **No company- or product-specific content.** Any company in any industry should be able to use the skill.
- **Be concrete.** Give real thresholds, real commands and real file names. "Consider checking performance" is useless. "Run `npx knip --reporter compact`; treat anything it lists as a candidate, never as proof" is useful.
- **Verification over assertion.** Code skills prove their result: tests pass, build is green, or the script output is shown. Content skills self-check against an explicit checklist before returning.
- **Keep SKILL.md under ~350 lines.** Move long reference material to `references/` and link it with a relative path.
- **Scripts:** use only the standard library, keep them idempotent, and support `--help`. Never make network calls unless the skill exists to make them (e.g. an SEO crawler). Run every script at least once before committing.
- **People decisions (HR):** the skill assists and a human decides. It never infers protected characteristics. It flags jurisdiction-dependent law and tells the user to check it rather than stating it as settled.

## Quality bar

`scripts/review-rubric.md` defines the scoring. A skill ships only at **≥ 8/10**.
