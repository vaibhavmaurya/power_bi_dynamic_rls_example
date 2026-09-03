# Architecture

```text
                  Microsoft Entra ID
                         |
                    Security groups
                         |
             membership / entitlement sync
                         |
                         v
                  Databricks Delta
         +---------------+---------------+
         |                               |
 security.user_access                 mart.sales
 user_upn                             region_key
 region_key                           ...
         |                               |
         +---------------+---------------+
                         |
                         v
              Power BI semantic model
                         |
       DynamicUserSecurity RLS role
                         |
 LOWER(UserAccess[user_upn])
 = LOWER(USERPRINCIPALNAME())
                         |
                         v
                  secured report
```

## GitOps control plane

```text
PBIP/TMDL + RLS + config
          |
          v
        GitHub
          |
        PR review
          |
          v
    GitHub Actions
          |
   GitHub OIDC -> Entra
          |
          v
   Fabric REST / Power BI REST
          |
       Workspace
```

## Security boundaries

Workspace access decides who can access authoring/workspace resources.

RLS decides which rows a consumer can query.

Do not use visual hiding as the security boundary. If a visual contains sensitive data,
protect the underlying model with RLS/OLS.
