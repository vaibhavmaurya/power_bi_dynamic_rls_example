# Authentication

## Primary implementation — Service Principal (CI/CD default)

```
Authentication:  OAuth 2.0 Client Credentials
Identity:        Microsoft Entra Service Principal
Python Library:  msal
MSAL Application: ConfidentialClientApplication
Authority:       https://login.microsoftonline.com/<tenantId>
Scope:           https://api.fabric.microsoft.com/.default
Token Method:    acquire_token_for_client()
```

Implemented in `src/authentication.py::ServicePrincipalTokenProvider`. This is the only
authentication mechanism used by the GitHub Actions workflows in this repository. MSAL caches
tokens internally and only requests a new one when necessary.

Credentials are supplied exclusively via environment variables / GitHub Actions secrets, never
via project or environment JSON:

```
FABRIC_TENANT_ID
FABRIC_CLIENT_ID
FABRIC_CLIENT_SECRET
```

## Optional — Interactive user authentication (local dev / troubleshooting only)

```
Authentication:   OAuth delegated user authentication
MSAL Application: PublicClientApplication
Scope:            https://api.fabric.microsoft.com/SemanticModel.ReadWrite.All
```

Implemented in `src/authentication.py::InteractiveUserTokenProvider`. Intended for local
development, API troubleshooting, and administrative/developer validation — **never** used as
the default GitHub CI/CD authentication method.

## Abstraction

Fabric client code depends only on the `TokenProvider` interface
(`src/authentication.py::TokenProvider`), never on a specific MSAL application type, so the
authentication mechanism (service principal, interactive user, device code, certificate,
workload identity federation) can change without touching `src/fabric_client.py` or
`src/deploy.py`.

## Security requirements

The application must never log client secrets, access/refresh tokens, GitHub secrets, or
complete Base64 semantic-model payloads. Client-secret authentication via MSAL is acceptable
for this POC; a production evolution can move to certificate authentication or workload
identity federation without changing the deployment architecture.
