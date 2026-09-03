# V4 Solution

## Runtime
`Power BI login -> USERPRINCIPALNAME() -> Dynamic RLS -> Databricks UserAccess -> authorized rows`

Example RLS:

```DAX
LOWER(UserAccess[user_upn]) = LOWER(USERPRINCIPALNAME())
```

## Entra group
Optional. Use it for report/app access or bulk membership of the Power BI RLS role. It is not the source of region/business entitlement.

## PBIX
PBIX is sufficient. Define and test RLS in Power BI Desktop, publish the PBIX, then add intended users or a security group to the RLS role in Power BI Service.
