# Code review findings - v1 -> v2

## Fixed

1. `definition.pbism` is required for a semantic-model public definition.
2. Validation now requires a complete TMDL model (`database.tmdl`, `model.tmdl`, tables, role).
3. RLS role syntax changed to documented `tablePermission Table = DAX`.
4. Service-principal refresh no longer sends `notifyOption`.
5. Fabric pagination now follows `continuationUri`.
6. REST calls retry throttling/transient failures.
7. Long-running operation URLs can be relative or absolute.
8. Added semantic-model definition export/bootstrap script.
9. Added semantic-model connection binding script.
10. Deployment workflow binds connections before refresh.
11. RLS role membership is explicitly surfaced as a governance prerequisite.

## Still intentionally external / environment-specific

- Actual Databricks connection object creation and credentials.
- Exact Databricks connection `type` and `path` values.
- RLS role membership automation if your organization wants it via XMLA/TMSL.
- Power BI app publishing/audience management.
- Report PBIR deployment.
- Automated end-to-end RLS impersonation testing.
- Sensitivity labels and endorsement/certification.
