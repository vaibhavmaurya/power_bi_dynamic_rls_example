role DynamicUserSecurity
	modelPermission: read

	tablePermission UserAccess =
		LOWER(UserAccess[user_upn]) = LOWER(USERPRINCIPALNAME())

{{MEMBERS}}
