# Power BI / Microsoft Fabric RLS Governance

Centralized governance, validation, and deployment of Power BI / Microsoft Fabric semantic
model Row-Level Security (RLS) definitions, driven by GitHub pull requests and deployed via
Microsoft Fabric REST APIs. See [`specification.md`](specification.md) for the full design and
[`CLAUDE.md`](CLAUDE.md) / [`docs/architecture.md`](docs/architecture.md) for an implementation
summary.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in FABRIC_TENANT_ID / FABRIC_CLIENT_ID / FABRIC_CLIENT_SECRET for local testing
```

## Run tests

```bash
pytest tests/ -v
```

## Deploy locally (manual/troubleshooting)

```bash
python -m src.main \
  --project projects/sales/project.json \
  --environment projects/sales/environments/dev.json \
  --base-ref origin/main
```

Requires `FABRIC_TENANT_ID`, `FABRIC_CLIENT_ID`, `FABRIC_CLIENT_SECRET` to be set in the
environment, and `projects/sales/environments/dev.json` to point at a real workspace/semantic
model.

## Docs

- [`docs/architecture.md`](docs/architecture.md) — module-by-module architecture
- [`docs/fabric-api-reference.md`](docs/fabric-api-reference.md) — the five Fabric REST APIs used
- [`docs/authentication.md`](docs/authentication.md) — MSAL / Entra ID authentication design
- [`docs/github-cicd.md`](docs/github-cicd.md) — workflows, branch protection, required secrets
