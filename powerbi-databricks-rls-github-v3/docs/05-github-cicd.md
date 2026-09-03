# GitHub CI/CD

## Authentication

Use GitHub OIDC, not a long-lived client secret.

GitHub Environment variables:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`

The Entra application needs a federated credential matching the repository/environment.

## Pipeline sequence

1. Validate config/source.
2. Azure login through OIDC.
3. Acquire Fabric and Power BI API tokens.
4. Reconcile workspace role assignments.
5. Render environment-specific TMDL role membership into `.build/`.
6. Create/update semantic model from TMDL.
7. Bind the semantic model to the environment's Fabric connection.
8. Refresh the model.
9. Execute RLS tests in non-production.
10. Rewrite PBIR's semantic model reference in `.build/`.
11. Create/update the report.

## Why render into `.build/`?

Environment-specific IDs and group identities should not mutate the source tree during CI.
The source remains stable while the deployment artifact is materialized per environment.

## Promotion

Recommended:

```text
feature/* -> PR -> develop -> DEV
                      |
                      +-> protected TEST workflow dispatch
                      |
                      +-> protected PROD workflow dispatch
```

Use GitHub Environments with required reviewers for TEST/PROD and CODEOWNERS for security assets.
