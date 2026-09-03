# Automated RLS Testing

V3 supports security assertions such as:

```text
john@company.com -> expected INDIA, GERMANY
mary@company.com -> expected USA
```

The test sends a DAX query with:

- `effectiveUsername`
- the configured RLS role
- an expected value set

The response uses Apache Arrow and is parsed with `pyarrow`.

## Important platform prerequisite

The DAX query API has tenant/permission limitations. The deployment identity must be permitted to
use the query API and to provide the role/effective username as documented by Microsoft.

Do not downgrade a failed or unsupported RLS test to "green". If the tenant does not allow this
automation, use a delegated/admin test identity or a separate XMLA-based test stage and record
that as an explicit architecture decision.

## Recommended test classes

- Positive: user sees allowed region.
- Negative: user cannot see a forbidden region.
- Empty entitlement: user receives zero protected rows.
- Multi-region: user receives exactly the configured set.
- Expired entitlement: expired row is not visible.
- Case-normalization: UPN case differences do not change authorization.
