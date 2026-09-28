# GitHub CI/CD

For the concrete, step-by-step setup (creating the GitHub Environments, adding secrets,
configuring branch protection, and walking through a real PR end to end — including the
solo-maintainer approval flow), see
[`docs/pull-request-workflow.md`](pull-request-workflow.md). This page covers the workflow
files themselves at a reference level.

## Workflows

### `.github/workflows/pr-dev.yml` — RLS / DEV Deployment

Triggers on `pull_request` (`opened`, `synchronize`, `reopened`) targeting `main`. Runs
`python -m src.main` against `projects/sales/environments/dev.json`, diffing changed `.tmdl`
role files against the PR's base ref. The job name (`RLS / DEV Deployment`) is what should be
configured as a required status check on the `main` branch protection rule, alongside required
reviewer approval (see CODEOWNERS below) — a failed deployment must block merge.

Concurrency group: `sales-dev` (one deployment per project+environment at a time, per spec
section 26).

### `.github/workflows/promote.yml` — RLS Promotion

Triggers on `push` to `main` (i.e., after a PR merges). Runs three sequential jobs —
`deploy-test`, `deploy-uat`, `deploy-prod` — each targeting the matching environment JSON file
and each declared with a GitHub `environment:` (`TEST` / `UAT` / `PROD`). Configure required
reviewers on those GitHub Environments in repository settings to get the IT/Security →
Business/Viz Owner → Production/Security Owner approval chain from spec section 31. Each job
has its own concurrency group (`sales-test` / `sales-uat` / `sales-prod`).

The same merged commit's role files are deployed unchanged at every stage — only the
`--environment` file (and therefore `workspaceId`/`semanticModelId`) changes.

Note: the promotion workflow currently diffs each stage's role changes against `HEAD~1` (the
immediately preceding commit) as a POC-level simplification. If a squash-merged PR contains
role changes that don't fall in the immediate parent diff, extend `_git_changed_files` in
`src/main.py` to diff against the last commit successfully deployed to that specific
environment instead.

## Branch protection / review

- `.github/CODEOWNERS` requires `@rls-security-team` review on any change under
  `/projects/**/roles/`. This assumes a team distinct from the PR author; for a solo
  maintainer, GitHub cannot self-approve a PR review at all, so
  [`docs/pull-request-workflow.md`](pull-request-workflow.md) uses the required DEV status
  check plus per-environment deployment approvals as the gate instead of a required PR review.
- Once a real reviewer team exists, the `main` branch protection rule should require both a
  successful `RLS / DEV Deployment` check and CODEOWNERS approval before merge.

## Required secrets

Configure at the repository or environment level:

```
FABRIC_TENANT_ID
FABRIC_CLIENT_ID
FABRIC_CLIENT_SECRET
```

These must never appear in `project.json`, any `environments/*.json` file, or workflow logs.
