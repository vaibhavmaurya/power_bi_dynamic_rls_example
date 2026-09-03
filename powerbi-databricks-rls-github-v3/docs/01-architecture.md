# Architecture

## Data plane

```text
Microsoft Entra ID
      |
      +-- User identity
      +-- Security groups
              |
              v
Databricks entitlement process
              |
              v
security.user_access
(user_upn, region_key, active dates)
              |
              v
Power BI semantic model
  DynamicUserSecurity
  UserAccess[user_upn] = USERPRINCIPALNAME()
              |
              v
Relationship propagation
UserAccess[region_key] 1 -> * Sales[region_key]
              |
              v
Power BI report (PBIR)
```

## Control plane

```text
GitHub repository
  |
  +-- TMDL
  +-- PBIR
  +-- RLS group members
  +-- environment config
  +-- tests
  +-- workflows
  |
  v
Pull request / CODEOWNERS
  |
  v
GitHub Actions
  |
  +-- OIDC -> Entra
  +-- Fabric REST
  +-- Power BI REST
  |
  v
DEV -> TEST -> PROD
```

## Why two authorization layers?

Workspace access answers: **Can the principal access the Power BI/Fabric content?**

RLS answers: **Which rows may that principal query?**

A user can be a report consumer but still receive no rows unless RLS resolves an entitlement.
Conversely, do not use RLS to compensate for excessive workspace Admin/Member/Contributor access.
