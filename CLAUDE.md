# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

This repository currently contains only `specification.md` (the full spec) and `check.txt`
(local test credentials/sample RLS role — see below). No application code has been written yet;
the codebase described below is the target architecture to implement, not existing structure.

## What this project is

A centralized governance system for Power BI / Microsoft Fabric **Semantic Model Row-Level
Security (RLS)** definitions. Scope is intentionally restricted to RLS only — report
development, measures, tables, relationships, Power Query, and general semantic-model design
are out of scope. RLS TMDL files live in GitHub (source of truth for governed RLS); the full
semantic model lives in Microsoft Fabric (source of truth for everything else). Deployment
flows through Microsoft Fabric REST APIs (never XMLA/TOM), authenticated via Microsoft Entra
ID OAuth 2.0 using MSAL Python with a Service Principal (client-credentials flow) as the
primary CI/CD identity.

Read `specification.md` in full before implementing — it is the authoritative design document
and includes exact API request/response shapes, pseudo-code, and acceptance scenarios.

## Core architectural invariant

`updateDefinition` **overrides** the entire semantic-model definition it is given. The
non-negotiable flow is therefore always:

```
Get complete Fabric semantic model definition
  → Overlay changed RLS role part(s) only (replace-by-path or append)
  → Preserve every other definition part byte-for-byte
  → Submit the complete updated definition
  → Re-read the definition
  → Verify deployed RLS content against Git
```

The single most important test invariant (spec §38): for every definition part that is **not**
a requested RLS target path, `BEFORE.path == AFTER.path` and `BEFORE.payload == AFTER.payload`.

## Planned repository structure (spec §4)

```
projects/<project-key>/
  project.json                  # roleSourcePath, roleDefinitionPathPrefix
  roles/*.tmdl                  # RLS role source files (source of truth)
  environments/{dev,test,uat,prod}.json   # workspaceId + semanticModelId only — no secrets

src/
  authentication.py   # TokenProvider abstraction (ABC) + ServicePrincipalTokenProvider /
                       # InteractiveUserTokenProvider implementations
  fabric_client.py    # FabricClient — thin wrapper over the 5 approved Fabric REST APIs
  lro.py               # single shared long-running-operation poller (Retry-After aware)
  change_detection.py # detects which project(s)/role file(s) changed in a PR/commit
  role_overlay.py     # overlay_role(): replace-by-path or append into definition.parts[]
  deploy.py            # orchestrates: auth → get model → get definition → overlay → update → verify
  verify.py            # post-deployment: re-read definition, decode, normalize, compare to Git

tests/                 # one test file per src module (see Unit Test Requirements below)
docs/                  # architecture.md, fabric-api-reference.md, authentication.md, github-cicd.md
.github/workflows/     # pr-dev.yml (PR → DEV), promote.yml (TEST → UAT → PROD with approval gates)
.github/CODEOWNERS     # /projects/**/roles/ requires review from the RLS/security team
```

Multiple role changes in one deployment must be overlaid onto a single definition and sent via
**one** `updateDefinition` call — never one call per role file (spec §24).

## Environment vs. authentication config (must stay separate)

- Environment JSON files (`dev.json`, `test.json`, `uat.json`, `prod.json`) hold only
  `workspaceId` and `semanticModelId`.
- Authentication config (`tenantId`, `clientId`, `clientSecret`) comes only from environment
  variables / GitHub secrets (`FABRIC_TENANT_ID`, `FABRIC_CLIENT_ID`, `FABRIC_CLIENT_SECRET`),
  never from project or environment JSON.
- `check.txt` in the repo root contains sample/local values for these plus one example RLS role
  TMDL snippet, for manual local testing only (per commit history these are placeholder/fake
  values, not live credentials) — never copy its contents into committed config files.

## Fabric REST API surface (spec §12) — do not expand beyond this list

| Purpose | Method | Path |
|---|---|---|
| Verify semantic model | GET | `/workspaces/{workspaceId}/semanticModels/{semanticModelId}` |
| Get definition | POST | `/workspaces/{workspaceId}/semanticModels/{semanticModelId}/getDefinition?format=TMDL` |
| Poll LRO state | GET | `/operations/{operationId}` |
| Get LRO result | GET | `/operations/{operationId}/result` |
| Update definition | POST | `/workspaces/{workspaceId}/semanticModels/{semanticModelId}/updateDefinition` |

Base URL: `https://api.fabric.microsoft.com/v1`. Both Get Definition and Update Definition may
return `202 Accepted` with `Location` / `x-ms-operation-id` / `Retry-After` headers — route all
polling through one shared LRO handler (`FABRIC_LRO_TIMEOUT_SECONDS`, default 900) that respects
`Retry-After`, including on `429` responses.

## Deployment/promotion model

- **DEV**: auto-deployed on every PR (opened/synchronize/reopened against `main`); this is what
  validates the change. Required PR check name: `RLS / DEV Deployment`.
- **TEST / UAT / PROD**: only ever receive the exact Git commit SHA already merged and validated
  in DEV — the role TMDL is never regenerated or modified per environment. Each gate requires
  GitHub Environment approval (IT/Security → Business/Viz Owner → Production/Security Owner).
- Concurrency: GitHub Actions concurrency groups should be scoped per `project + environment`
  (e.g. `sales-dev`, `sales-prod`) to prevent parallel deployments to the same target.
- Concurrent-change protection: before applying the overlay, re-fetch the definition and diff
  all non-target parts against the first read; abort (`CONCURRENT_MODEL_CHANGE_DETECTED`) if
  anything outside the target role path(s) changed between reads.

## Explicitly out of scope

Role/RLS **deletion** and **rename** are rejected outright in this POC (removing `abc.tmdl` from
Git must never delete the corresponding Fabric role) — only ADD and UPDATE (replace) are
supported. See spec §34 and the non-goals in §44 before adding any delete/rename behavior.

## Unit test coverage (spec §38)

Tests must cover, per module: SP auth success/failure, replace vs. append role-overlay
behavior, multi-role single-update behavior, non-RLS part preservation, base64 round-trip,
duplicate-role-path rejection, role-deletion rejection, 200 vs. 202 paths for both Get and
Update Definition, LRO Running→Succeeded/Failed/timeout, 429/Retry-After handling, concurrent
non-RLS change detection, and post-deployment verification.
