# Architecture

See `specification.md` at the repository root for the full design document. This page
summarizes how the `src/` modules map onto that design.

## Module responsibilities

| Module | Responsibility |
|---|---|
| `src/authentication.py` | `TokenProvider` abstraction + Service Principal / interactive-user MSAL implementations |
| `src/fabric_client.py` | Thin wrapper over the five approved Fabric REST APIs; routes 202 responses through the shared LRO poller |
| `src/lro.py` | Single shared long-running-operation poller (`Retry-After`-aware, configurable timeout) |
| `src/role_overlay.py` | `overlay_role` / `overlay_roles` — replace-by-path or append RLS parts into a definition |
| `src/change_detection.py` | Determines which `.tmdl` role files changed in a diff; rejects delete/rename |
| `src/verify.py` | Post-deployment comparison of deployed Base64 payloads against Git content |
| `src/deploy.py` | Orchestrates: get model → get definition (x2, concurrency check) → overlay → update → re-verify |
| `src/config.py` | Loads `project.json` / environment JSON / auth env vars, keeping the two concerns separate |
| `src/main.py` | CLI entry point invoked by GitHub Actions; prints the PR/deployment report |
| `src/errors.py` | The error-code model from spec section 36 |

## Deployment flow (`src/deploy.py::deploy_roles`)

```
Get Semantic Model
      |
Get Definition (D0)
      |
Get Definition again (D1)
      |
Diff non-target parts of D0 vs D1  --changed--> ConcurrentModelChangeDetectedError (abort)
      |
Overlay every changed role onto D1 (single pass)
      |
Update Definition once
      |
Get Definition again
      |
Verify every target role payload against Git content
```

This mirrors spec sections 19 and 24-27: multiple role changes in one deployment are always
combined into a single `updateDefinition` call, and every definition part outside the changed
role paths is preserved byte-for-byte because `updateDefinition` overrides whatever it is
given.

## Promotion model

DEV deploys automatically from `.github/workflows/pr-dev.yml` on every pull request. Merges to
`main` trigger `.github/workflows/promote.yml`, which deploys the same merged commit to TEST,
then UAT, then PROD in sequence, each gated by a GitHub Environment (`environment: TEST` /
`UAT` / `PROD`) with required reviewers configured in the repository settings — this is what
provides the approval gate described in spec section 31. The role TMDL content is never
regenerated per environment; only `workspaceId` and `semanticModelId` differ.
