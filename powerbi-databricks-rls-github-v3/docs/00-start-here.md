# Start Here

## What V3 solves

This repository treats Power BI security and reporting artifacts as governed software assets.
The semantic-model definition, DAX RLS rule, RLS group membership, report definition,
environment mapping, CI/CD logic and test expectations are reviewable in Git.

Operational business entitlements remain in Databricks, so adding an employee to a region
doesn't require a Power BI deployment.

## Separation of responsibility

| Layer | Owns |
|---|---|
| Microsoft Entra ID | Users, groups, authentication |
| Databricks | User/group-to-business-resource entitlements |
| TMDL semantic model | Relationships, measures, RLS rule, RLS role membership |
| PBIR | Report pages, visuals, filters, bookmarks, report settings |
| Fabric connection | Governed connection/credential object |
| GitHub | Version control, PR review, environment promotion |
| GitHub Actions | Deployment orchestration |

## First implementation sequence

1. Create/identify DEV, TEST and PROD Fabric/Power BI workspaces.
2. Create the deployment service principal and GitHub OIDC federated credential.
3. Give the deployment identity appropriate workspace/API permissions.
4. Create or identify the Databricks/Fabric connection in each environment.
5. Export the actual semantic model into `semantic-model/`.
6. Export the actual report into `report/`.
7. Merge the dynamic RLS role and validate the relationship direction.
8. Configure Entra RLS group membership in each environment JSON.
9. Configure workspace access principals.
10. Configure RLS test users and expected regions.
11. Open a PR; validation runs.
12. Merge to `develop` to deploy DEV.
13. Promote manually to TEST and PROD with protected GitHub environments.
