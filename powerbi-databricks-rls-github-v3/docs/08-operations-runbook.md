# Operations Runbook

## Add a new report consumer

1. Add the user to the Entra consumer group according to identity governance.
2. Add/update the business entitlement in Databricks.
3. No Power BI deployment is required if the group itself didn't change.

## Add a new RLS consumer group

1. Add the group to `semantic_model.rls.members` in the target environment config.
2. Open PR.
3. Security CODEOWNER approves.
4. Pipeline renders the TMDL member and deploys the semantic model.

## Change RLS logic

1. Update `templates/DynamicUserSecurity.tmdl.tpl`.
2. Add/update security test cases.
3. PR requires security-team approval.
4. Deploy DEV and verify.
5. Promote TEST then PROD.

## Rollback

Use Git revert to restore the last approved semantic-model/report/config state and redeploy.
Entitlement rollback in Databricks is a separate operational action.

## Incident: user sees too much data

1. Remove/revoke entitlement or group membership immediately using the identity/data authority.
2. Confirm user isn't a privileged workspace author.
3. Run the corresponding negative RLS test.
4. Review Git history for role/relationship/filter changes.
5. Review Databricks entitlement audit/change history.
