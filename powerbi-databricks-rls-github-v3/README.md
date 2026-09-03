# Proposed Approach – Dynamic Row-Level Security for Power BI using Databricks


# Power BI + Databricks Dynamic RLS - V3

V3 intentionally focuses on the actual RLS requirement.

```text
Logged-in Power BI user
        |
USERPRINCIPALNAME()
        |
Power BI Dynamic RLS
        |
Databricks UserAccess entitlement
        |
Authorized rows
```

## V3 simplification

Removed from the core solution: Entra group as a data-entitlement step, group membership embedded in TMDL, PBIR deployment, Fabric Connection lifecycle, and report deployment.

The report can remain a normal **PBIX**. An Entra security group is optional for report/app access or for assigning many consumers to the RLS role in Power BI Service. **Databricks remains the source of user-to-data entitlement.**

TMDL/GitHub CI/CD remains only as optional industrialization for the semantic model and RLS definition.
