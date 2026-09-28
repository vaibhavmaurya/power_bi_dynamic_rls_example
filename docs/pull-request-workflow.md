# Pull Request Workflow — Setup & Walkthrough

This is the step-by-step runbook for configuring GitHub so the RLS governance pipeline works
end to end: a pull request triggers automatic DEV deployment, merging promotes the same
commit through TEST → UAT → PROD, and each higher environment requires an explicit approval.

It assumes a **solo maintainer** setup (one person is both the PR author and the environment
approver). See [Section 0](#0-a-constraint-specific-to-solo-maintainers) for why that changes
a couple of the usual recommendations.

Repository referenced throughout: `vaibhavmaurya/power_bi_dynamic_rls_example`. Substitute
your own `<owner>/<repo>` where shown.

---

## 0. A constraint specific to solo maintainers

GitHub does **not** let you approve your own pull request — the "Approve" review option is
disabled on a PR you authored, and there is no setting that overrides this.

GitHub **Environment deployment approvals are different**: you *can* approve your own
deployment, as long as you're listed as a required reviewer for that environment. The design
below relies on that distinction:

- **Pull request review**: not required (you can't self-approve it anyway). The
  `RLS / DEV Deployment` status check stands in as the PR gate instead.
- **DEV**: deploys automatically on every PR, no approval gate.
- **TEST / UAT / PROD**: each is a GitHub Environment with "Required reviewers" set to your
  own account. You'll get a notification, open the workflow run, and approve it yourself.

**Plan check:** environment protection rules (required reviewers) are free on **public**
repositories. On a **private** repository they require GitHub Pro (personal accounts) or
Team/Enterprise (organizations). If you're on GitHub Free with a private repo, either make the
repo public or upgrade — otherwise TEST/UAT/PROD will deploy immediately without ever pausing
for your approval.

---

## 1. Rotate and collect real credentials

Before touching any GitHub settings, have these ready:

- `FABRIC_TENANT_ID`
- `FABRIC_CLIENT_ID`
- `FABRIC_CLIENT_SECRET` — must be a freshly rotated secret, not one that has ever been
  committed to this repository
- Per-environment `workspaceId` / `semanticModelId` for DEV, TEST, UAT, PROD (a single Fabric
  workspace can stand in for all four for a POC)

---

## 2. Create the four GitHub Environments

**github.com → your repo → Settings → Environments → New environment**. Create exactly these
four names (the workflow YAML files reference them by name):

- `DEV`
- `TEST`
- `UAT`
- `PROD`

**`DEV`**: leave "Deployment protection rules" empty — no reviewers, no wait timer. It must
deploy automatically per the design.

**`TEST`, `UAT`, `PROD`**: under "Deployment protection rules", enable **Required reviewers**
and add your own GitHub username to each. A wait timer is optional and can be left at 0.

Equivalent via the GitHub CLI (the UI is the more common path, but this scripts the reviewer
assignment):

```bash
OWNER_REPO="vaibhavmaurya/power_bi_dynamic_rls_example"
MY_ID=$(gh api user -q .id)

gh api --method PUT "repos/$OWNER_REPO/environments/TEST" \
  -f "reviewers[][type]=User" -F "reviewers[][id]=$MY_ID"
gh api --method PUT "repos/$OWNER_REPO/environments/UAT" \
  -f "reviewers[][type]=User" -F "reviewers[][id]=$MY_ID"
gh api --method PUT "repos/$OWNER_REPO/environments/PROD" \
  -f "reviewers[][type]=User" -F "reviewers[][id]=$MY_ID"
```

---

## 3. Add Fabric credentials as environment secrets

For **each** of the four environments (Settings → Environments → click the environment name →
"Environment secrets" → **Add secret**), add:

| Secret name | Value |
|---|---|
| `FABRIC_TENANT_ID` | your tenant ID |
| `FABRIC_CLIENT_ID` | your rotated client ID |
| `FABRIC_CLIENT_SECRET` | your rotated client secret |

Or via CLI (prompts interactively for the value, so nothing sensitive ends up in shell
history):

```bash
for ENV in DEV TEST UAT PROD; do
  gh secret set FABRIC_TENANT_ID     --env "$ENV" --repo "$OWNER_REPO"
  gh secret set FABRIC_CLIENT_ID     --env "$ENV" --repo "$OWNER_REPO"
  gh secret set FABRIC_CLIENT_SECRET --env "$ENV" --repo "$OWNER_REPO"
done
```

Also update `projects/sales/environments/{dev,test,uat,prod}.json` with your real
`workspaceId` / `semanticModelId` values. These are not secrets — commit them normally.

---

## 4. Configure branch protection on `main`

**Settings → Branches → Add branch protection rule**, branch name pattern `main`:

- ✅ **Require status checks to pass before merging** → select `RLS / DEV Deployment`. This
  check only appears in the picker after the workflow has run at least once — open one PR
  first, then come back and add it if it isn't listed yet.
- ✅ **Require branches to be up to date before merging**
- ❌ Do **not** enable "Require a pull request before merging → Require approvals" with a
  count ≥ 1 — you cannot self-approve, so that setting would permanently lock you out of
  merging your own PRs. If you want a PR gate at all, enable "Require a pull request before
  merging" but leave the required-approvals count at 0.
- Leave **"Require review from Code Owners" off** for the same reason.
  `.github/CODEOWNERS` currently points at `@rls-security-team`, which doesn't exist for a
  solo repository — either edit that file to your own username for documentation purposes, or
  leave it as a placeholder for when a real reviewer team exists, but don't wire it into a
  required-review setting while you're the only maintainer.

---

## 5. Make sure approval emails actually reach you

**github.com → Settings (your account, not the repo) → Notifications** → under **Actions**,
confirm email delivery is enabled, not just the in-app bell icon. GitHub automatically emails
required reviewers when a deployment is waiting; this setting only controls whether that
email actually gets delivered to you.

---

## 6. End-to-end walkthrough

### 6.1 Create a feature branch and change a role

```bash
git checkout -b update-dynamic-user-security
# edit projects/sales/roles/DynamicUserSecurity4.tmdl (or add/modify any other .tmdl role file)
git add projects/sales/roles/DynamicUserSecurity4.tmdl
git commit -m "Update DynamicUserSecurity4 RLS role"
git push -u origin update-dynamic-user-security
```

### 6.2 Open the pull request

```bash
gh pr create --base main --fill
```

or via the web UI.

### 6.3 DEV deploys automatically

The `RLS / DEV Deployment` workflow (`.github/workflows/pr-dev.yml`) fires on
`opened`/`synchronize`/`reopened`, runs against the `DEV` environment and its secrets, and
posts its result as a required status check on the PR. A failed deployment fails the check and
blocks merge (per branch protection in Section 4).

### 6.4 Merge the pull request

Once the DEV check is green, merge it yourself — no separate approver is required, by design
(Section 0).

### 6.5 Promotion kicks off automatically

`promote.yml` triggers on `push` to `main`. Its first job, `deploy-test`, is bound to
`environment: TEST`, which has your required-reviewer rule attached — the job stops in a
**"Waiting"** state instead of running immediately.

### 6.6 Approve TEST

You receive an email: "Deployment review needed for TEST". Either follow that link, or go to
the **Actions** tab → the running workflow → you'll see a **"Review deployments"** banner →
check `TEST` → **Approve and deploy**.

### 6.7 Approve UAT, then PROD

Once `deploy-test` finishes, `deploy-uat` pauses the same way for `UAT` — approve it
identically. Then `deploy-prod` pauses for `PROD` — approve it too. After that approval, the
exact same Git commit that passed DEV validation has now been deployed and verified across
DEV, TEST, UAT, and PROD.

---

## Summary checklist

- [ ] Fabric Service Principal secret rotated (not the one ever committed to this repo)
- [ ] `DEV`, `TEST`, `UAT`, `PROD` GitHub Environments created
- [ ] `DEV` has no required reviewers; `TEST`/`UAT`/`PROD` have you as a required reviewer
- [ ] `FABRIC_TENANT_ID` / `FABRIC_CLIENT_ID` / `FABRIC_CLIENT_SECRET` set as environment
      secrets on all four environments
- [ ] `projects/sales/environments/*.json` updated with real `workspaceId` /
      `semanticModelId` values
- [ ] Branch protection on `main` requires the `RLS / DEV Deployment` status check, with
      required PR approvals left at 0
- [ ] Email notifications enabled for Actions under your GitHub account settings
- [ ] One PR opened and merged successfully to confirm the whole chain end to end
