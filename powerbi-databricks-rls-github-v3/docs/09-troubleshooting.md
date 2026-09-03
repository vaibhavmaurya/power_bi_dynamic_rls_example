# Troubleshooting

## User sees all rows

Check:

- Is the user a workspace Admin/Member/Contributor?
- Is the role deployed?
- Is the user/group a member of the role?
- Does `USERPRINCIPALNAME()` match the UPN stored in `UserAccess`?
- Does the security relationship propagate in the correct direction?
- Was the model accidentally deployed with a permissive role filter?

## User sees no rows

Check:

- User is in the TMDL role member group.
- Active entitlement exists.
- UPN normalization.
- Region keys match.
- Relationship is active.
- Refresh/imported entitlement data is current.

## bindConnection fails

The API requires the semantic-model owner and one call per data-source reference. Verify the
connection ID, connectivity type, connection details type/path, and ownership.

## PBIR deployment fails

Verify the exported report is actually PBIR format, `definition.pbir` exists, the `definition/`
folder exists, and the semantic model ID inserted into `datasetReference.byConnection` is valid.

## RLS test API returns errors

Check tenant settings, dataset compatibility, workspace-admin rights for effective username/role,
and whether the semantic model/source uses features with query API restrictions.
