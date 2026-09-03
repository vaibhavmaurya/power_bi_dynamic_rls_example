# Implementation

1. Maintain `UserAccess` entitlement data in Databricks.
2. Connect Power BI to entitlement and business tables.
3. Configure secure relationship/filter propagation.
4. Create `DynamicUserSecurity` in Power BI Desktop.
5. Apply `LOWER(UserAccess[user_upn]) = LOWER(USERPRINCIPALNAME())`.
6. Test with **View as / Other user**.
7. Publish the PBIX.
8. Add users or an Entra security group to the RLS role in Power BI Service.
9. Keep consumers as Viewer/app consumers; RLS does not restrict workspace Admin/Member/Contributor.
10. Validate in Power BI Service.

Role membership answers **who is evaluated under the RLS role**. Databricks entitlement answers **which business rows that user may see**.
