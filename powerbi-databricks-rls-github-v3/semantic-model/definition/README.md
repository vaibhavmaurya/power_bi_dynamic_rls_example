# Complete TMDL definition goes here

This directory must contain the full public TMDL definition of the semantic model, for example:

```text
definition/
├── database.tmdl
├── model.tmdl
├── relationships.tmdl
├── expressions.tmdl
├── roles/
│   └── DynamicUserSecurity.tmdl
└── tables/
    ├── UserAccess.tmdl
    └── Sales.tmdl
```

Keep the dynamic RLS role:

```DAX
LOWER(UserAccess[user_upn]) = LOWER(USERPRINCIPALNAME())
```

Model relationship:

```text
UserAccess[region_key]  1 ---- *  Sales[region_key]
```

The security filter must be able to propagate from `UserAccess` to the secured business table.

Do not put credentials in the TMDL files.
