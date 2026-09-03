# Power BI + Databricks Dynamic RLS GitOps - V3

V3 is an end-to-end reference implementation for managing a Databricks-backed Power BI
semantic model and report using GitHub.

It covers:

- Databricks Delta entitlement tables.
- Dynamic Power BI row-level security (RLS) using `USERPRINCIPALNAME()`.
- Microsoft Entra security-group membership serialized into the TMDL role.
- TMDL semantic-model source control.
- PBIR report source control and deployment.
- DEV / TEST / PROD configuration.
- GitHub OIDC authentication to Microsoft Entra ID.
- Fabric workspace access reconciliation.
- Semantic-model create/update.
- Fabric connection binding.
- Dataset refresh.
- Automated RLS positive/negative validation.
- Report rebind and create/update.
- Pull-request governance with CODEOWNERS.

## Runtime authorization

```text
User signs in
    |
USERPRINCIPALNAME()
    |
DynamicUserSecurity role
    |
UserAccess[user_upn] filter
    |
UserAccess[region_key] -> Sales[region_key]
    |
Only authorized rows
```

## GitOps deployment

```text
Developer -> PR -> validation -> approval -> GitHub Actions
                                        |
                                        +-> OIDC -> Entra
                                        +-> Workspace access
                                        +-> Render RLS role + group members
                                        +-> Deploy TMDL
                                        +-> Bind Fabric connection
                                        +-> Refresh
                                        +-> RLS tests
                                        +-> Rebind PBIR
                                        +-> Deploy report
```

Start with `docs/00-start-here.md`.
