# Ticket fetch — per tracker

Read this in Phase 0 (fetch) and Phase 2 (reading the plan and the review).
Use whichever access works in this session; if none does, ask the user to
paste the ticket **with its comments and linked-doc text**. Never work from a
remembered or guessed ticket. Never print or log a token.

## Fetching

| Tracker | Command (needs) | Notes |
|---|---|---|
| GitHub Issues | `gh issue view <n> --repo <owner/repo> --json number,title,body,labels,state,comments,updatedAt,url,parent,subIssues,closedByPullRequestsReferences` (`gh auth status` OK) | Linked PRs: `closedByPullRequestsReferences`; PRs that only mention it: `gh pr list --repo <owner/repo> --state all --search "<n> in:body"` (matches any body containing the number; confirm each); review threads: `gh pr view <pr> --comments` and `gh api repos/<owner>/<repo>/pulls/<pr>/comments` |
| GitLab Issues | `glab issue view <n> --comments` (`glab auth status` OK); JSON: `glab api projects/<url-encoded-path>/issues/<n>` and `.../issues/<n>/notes` | Linked MRs: `glab api projects/<id>/issues/<n>/related_merge_requests`; MR threads: `glab mr view <mr> --comments` |
| Jira Cloud/DC (REST) | `curl -sf -u "$JIRA_EMAIL:$JIRA_API_TOKEN" "$JIRA_BASE_URL/rest/api/3/issue/<KEY>?fields=summary,description,status,issuetype,components,labels,comment,subtasks,issuelinks,attachment,parent,updated&expand=renderedFields"` | v3 returns `description` as ADF JSON; read `renderedFields` (HTML) instead. Data Center uses `/rest/api/2/` and a PAT (`-H "Authorization: Bearer $JIRA_PAT"`). Linked PRs: `/rest/api/3/issue/<KEY>/remotelink` |
| Jira (CLI) | `jira issue view <KEY> --comments 100 --plain` (jira-cli, `jira me` OK) | Or any Jira integration your agent already has |
| Linear | `curl -sf https://api.linear.app/graphql -H "Authorization: $LINEAR_API_KEY" -H 'Content-Type: application/json' -d '{"query":"{ issue(id: \"<KEY>\") { identifier title description state { name } updatedAt labels { nodes { name } } parent { identifier description } comments { nodes { body createdAt user { name } } } children { nodes { identifier title } } attachments { nodes { url title } } } }"}'` | `id` accepts the identifier (`ENG-123`); personal keys go in `Authorization` without `Bearer`; attachments carry linked PRs; no issue type, use labels |
| Azure Boards | `az boards work-item show --id <n> --expand all --output json` (`az devops` extension, `az devops configure` defaults) | Comments: `curl -sf -u ":$AZURE_DEVOPS_PAT" "https://dev.azure.com/<org>/<project>/_apis/wit/workItems/<n>/comments?api-version=7.1-preview.4"`; page with `continuationToken` until `count` reaches `totalCount` |
| Pasted text | — | Record `Ticket updated: pasted at <time>`; ask for comments and linked docs if they aren't in the paste |

Fields you need before Setup: id, type (bug/feature/task), summary, `updated`.
If the response shows more comments than it returned (Jira `comment.total`,
paged APIs), page through them or say how many were not read.

## The plan — where to look

- Title, description, and the acceptance criteria section (headings such as
  "Acceptance criteria", "AC", "Definition of done", Given/When/Then blocks,
  task-list checkboxes in GitHub/GitLab bodies, or a dedicated custom field).
- Subtasks/child issues; for a subtask, also the parent's description.
- Linked spec, design or plan docs. Read them if your session can (a docs
  integration, a public URL); otherwise list each one under "sources that
  failed to load".
- Design files (Figma etc.) only for UI work, and only if a design tool is
  available; otherwise ask for screenshots.

## The review — sources to check

Record what each gave, even when empty:

- Comments that change scope or approach (not status pings, "+1", bot notices).
- Linked docs whose title or body marks them as a review (architecture/design/tech review, ADR, RFC).
- Review threads on linked PRs/MRs (earlier attempts, spikes).

None → `Review: none found (checked: comments, linked docs, PRs)`. Do not
promote an ordinary comment to "the review".

## Prior work & resume (Phase 1)

- Local branch: `git branch --list '*<ID>*'` (bare number: `'*/<n>-*'`).
- Remote branch: `git fetch origin && git branch -r --list '*<ID>*'`.
- PRs/MRs linked from the ticket (fields above).
- `.devloop/<ID>/brief.md` in this checkout and in every path from `git worktree list`.
- Uncommitted changes (`git status --porcelain`) in files the ticket names: may be the user's own start on this ticket.

A brief exists → read it, compare its `Fetched:` time with the ticket's
`updated`, and list what changed (new comments, edited ACs); continue from the
last completed phase if the user agrees. Pasted tickets can't be compared: ask
the user whether anything changed.
