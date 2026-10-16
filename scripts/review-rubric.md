# Skill review rubric

Score each criterion 1-10. **Overall = weighted mean, rounded to one decimal place.** Ship at ≥ 8.0, and only when no single criterion is below 6.

| # | Criterion | Weight | 10 looks like |
|---|---|---|---|
| 1 | **Triggering** | 10% | The description starts "Use when", lists the real phrases and symptoms users type, says nothing about the workflow, and doesn't overlap sibling skills |
| 2 | **Actionability** | 20% | An agent new to the topic could follow the steps with no guessing. Each step has real commands or criteria and a check that says it's done |
| 3 | **Correctness** | 20% | Commands, flags, tool names, thresholds and domain facts are accurate as of 2026. Nothing is invented |
| 4 | **Output contract** | 15% | The deliverable's shape is fixed and predictable, and the user can act on it straight away |
| 5 | **Guardrails & edge cases** | 15% | Destructive or people-affecting actions are gated. The likely failure modes are named and handled (monorepos, no tests, missing input, legal limits) |
| 6 | **Portability** | 10% | No harness-specific tool names and no company specifics. Works in Claude Code, Codex, Cursor and Antigravity. Non-code skills also work in plain chat |
| 7 | **Concision** | 10% | No filler, no repetition, and every line earns its tokens. SKILL.md is ≤ ~350 lines, with heavy reference moved to `references/` |

## Review procedure

1. Read the skill cold.
2. **Walk-through test:** pick a realistic, slightly messy scenario (for example a pnpm monorepo, a Gradle multi-module build, a JD for a role with vague requirements). Follow the skill step by step as the agent would. Write down every point where you had to guess, every step that was wrong, and every place the output would be weak.
3. If the skill ships scripts, run them on a small fixture and confirm they work and that `--help` works.
4. Score each criterion with a one-line reason.
5. If the score is below 8, or any criterion is below 6, fix the skill directly and run steps 1-4 again. Stop when it passes, or after 3 rounds; if it still fails after 3 rounds, report what blocks it.
