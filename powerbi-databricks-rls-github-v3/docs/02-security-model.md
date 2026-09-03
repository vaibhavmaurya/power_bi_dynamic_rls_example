# Security Model

## Dynamic RLS

The generated role is conceptually:

```TMDL
role 'DynamicUserSecurity'
    modelPermission: read

    tablePermission UserAccess =
        LOWER(UserAccess[user_upn]) = LOWER(USERPRINCIPALNAME())

    member 'sg-powerbi-report-users-prod@company.com' = group
```

At runtime Power BI evaluates `USERPRINCIPALNAME()` for the signed-in consumer.

For John:

```text
john@company.com
  -> UserAccess rows for John
  -> INDIA, GERMANY
  -> relationship filters Sales
```

## Why keep entitlements in Databricks?

Do not serialize thousands of user-to-region assignments into Git. Git contains the policy;
Databricks contains dynamic business authorization data.

## Entra group vs business entitlement

The Entra group configured as the TMDL role member means:
"this principal population participates in DynamicUserSecurity."

The Delta entitlement table means:
"within that population, this user can see INDIA and GERMANY."

These solve different problems.

## Admin warning

RLS is designed for report consumers. Workspace Admin/Member/Contributor access is privileged
authoring/management access and must be tightly governed.

## Visual visibility

Use RLS/OLS for the security boundary. DAX visual-filter/show-hide logic may improve UX but must
not be the only protection for confidential data.
