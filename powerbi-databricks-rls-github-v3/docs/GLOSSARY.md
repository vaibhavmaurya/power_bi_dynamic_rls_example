# Glossary

| Term | Definition |
|---|---|
| PBIX | Standard Power BI Desktop report file; sufficient for RLS. |
| RLS | Row-Level Security; filters semantic-model rows for a user. |
| USERPRINCIPALNAME() | DAX function resolving the current user's UPN. |
| Entitlement | User-to-business-data authorization mapping, stored in Databricks here. |
| Entra Security Group | Optional for content access or bulk RLS-role membership; not the data-entitlement source. |
| TMDL | Text representation of the semantic model; useful for Git/CI-CD but optional for basic PBIX RLS. |
| PBIR | Source-control-friendly report format; out of scope in V4. |
| Fabric Connection | Governed datasource connection object; out of scope in V4's simplified solution. |
