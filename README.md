# Agent Skills

22 skills for developers, QA, AI engineers, SEO, HR and content teams. Each skill is a plain `SKILL.md` file, so it runs in **Claude Code, OpenAI Codex, Cursor and Google Antigravity**. The HR and content skills also work in a plain chat window.

Each skill was written to a [shared contract](CONTRIBUTING.md), then scored and fixed by a separate reviewer against a [rubric](scripts/review-rubric.md). A skill ships only at **8/10 or higher**. Bundled scripts use only the Python standard library and come with tests.

## Install

**Claude Code**
```
/plugin marketplace add srewoo/agent-skills
/plugin install qa-toolkit@agent-skills        # or any toolkit below
```

**Codex**
```
codex plugin marketplace add srewoo/agent-skills
```
Then open `/plugins` and install a toolkit.

**Cursor, Antigravity, or any agent: copy the skill folders**
```bash
git clone https://github.com/srewoo/agent-skills && cd agent-skills
./install.sh                                  # every skill, every agent, user-wide
./install.sh --agent cursor de-slop           # one skill, one agent
./install.sh --project --agent antigravity    # into the current repo's .agents/skills
./install.sh --list
```

| Agent | User-wide | Per project |
|---|---|---|
| Claude Code | `~/.claude/skills` | `.claude/skills` |
| Codex | `~/.agents/skills` | `.agents/skills` |
| Cursor | `~/.cursor/skills` | `.cursor/skills` |
| Antigravity | `~/.gemini/config/skills` | `.agents/skills` |

**Plain chat (claude.ai, ChatGPT, Gemini):** paste the skill's `SKILL.md` into the conversation, or upload it as a skill where the app supports that.

## Skills

### dev-toolkit
| Skill | Use it when |
|---|---|
| [dependency-upgrader](plugins/dev-toolkit/skills/dependency-upgrader/SKILL.md) | You're moving one dependency, framework or runtime across a major version (React 19, Spring Boot 3, Java 21, Python 3.12 …) |
| [pr-splitter](plugins/dev-toolkit/skills/pr-splitter/SKILL.md) | A branch is too big to review and needs to become a stack of small, green PRs |
| [dead-code-reaper](plugins/dev-toolkit/skills/dead-code-reaper/SKILL.md) | You want unused exports, files, dependencies or stale feature flags found and safely removed |

### qa-toolkit
| Skill | Use it when |
|---|---|
| [flaky-test-hunter](plugins/qa-toolkit/skills/flaky-test-hunter/SKILL.md) | A test passes and fails intermittently. It finds the cause and removes the non-determinism, with no sleeps or retries |
| [bug-report-to-repro](plugins/qa-toolkit/skills/bug-report-to-repro/SKILL.md) | A vague bug report needs exact repro steps and a failing test |
| [test-gap-finder](plugins/qa-toolkit/skills/test-gap-finder/SKILL.md) | You want to know which changed behaviour in a PR has no test |

### ai-eng-toolkit
| Skill | Use it when |
|---|---|
| [eval-builder](plugins/ai-eng-toolkit/skills/eval-builder/SKILL.md) | An LLM prompt, RAG system or agent needs an eval suite and pass rates |
| [prompt-regression](plugins/ai-eng-toolkit/skills/prompt-regression/SKILL.md) | You need a ship/no-ship verdict on a prompt, model or parameter change |
| [rag-debugger](plugins/ai-eng-toolkit/skills/rag-debugger/SKILL.md) | A RAG system returns wrong, missing or made-up answers |
| [llm-cost-auditor](plugins/ai-eng-toolkit/skills/llm-cost-auditor/SKILL.md) | The LLM bill is too high and you want savings ranked, with a check that quality holds |

### seo-toolkit
| Skill | Use it when |
|---|---|
| [technical-seo-audit](plugins/seo-toolkit/skills/technical-seo-audit/SKILL.md) | You need a crawl-based audit of indexing, canonicals, redirects, hreflang, schema and Core Web Vitals |
| [keyword-cluster](plugins/seo-toolkit/skills/keyword-cluster/SKILL.md) | A keyword export needs grouping by intent and mapping to pages, with cannibalisation flagged |
| [content-gap](plugins/seo-toolkit/skills/content-gap/SKILL.md) | You want the topics competitors cover and you don't, as prioritised content briefs |

### hr-toolkit
| Skill | Use it when |
|---|---|
| [jd-writer](plugins/hr-toolkit/skills/jd-writer/SKILL.md) | A job description needs to be inclusive, honest about requirements, and compliant with pay-transparency rules |
| [interview-kit](plugins/hr-toolkit/skills/interview-kit/SKILL.md) | You want a structured interview loop with anchored scoring rubrics |
| [resume-screener](plugins/hr-toolkit/skills/resume-screener/SKILL.md) | A batch of resumes needs scoring against a rubric, with evidence for each score. A human makes the decision |
| [policy-drafter](plugins/hr-toolkit/skills/policy-drafter/SKILL.md) | You need a plain-language workplace policy plus a list of points to check with legal |
| [onboarding-plan](plugins/hr-toolkit/skills/onboarding-plan/SKILL.md) | A new hire needs a 30/60/90-day plan |
| [feedback-rewriter](plugins/hr-toolkit/skills/feedback-rewriter/SKILL.md) | Feedback is harsh, vague or biased and needs to become specific and actionable |

### content-toolkit
| Skill | Use it when |
|---|---|
| [de-slop](plugins/content-toolkit/skills/de-slop/SKILL.md) | A draft sounds like AI. It removes the tells without changing the facts |
| [brand-voice](plugins/content-toolkit/skills/brand-voice/SKILL.md) | You want a voice guide built from samples, and drafts rewritten to match it |
| [repurposer](plugins/content-toolkit/skills/repurposer/SKILL.md) | One long piece needs turning into LinkedIn, X, newsletter, video and carousel content |

## Limits

- **HR skills** help a person decide; they never make the decision. Employment law differs by country and changes often, so every legal point in them is flagged for you to check with your own counsel.
- **Facts that go stale:** platform limits, SEO thresholds and tool flags were checked in October 2026. Re-check them before relying on them.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md). To check your changes, run:

```bash
python3 scripts/build_manifests.py   # regenerate the Claude Code and Codex manifests
python3 scripts/validate.py          # lint every SKILL.md; CI runs both
```

MIT licensed.
