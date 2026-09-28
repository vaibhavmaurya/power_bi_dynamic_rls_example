# Fabric API Based Centralized Power BI RLS Governance
## Technical Specification for POC

## 1. Objective

Build a centralized application and CI/CD process for managing **Power BI / Microsoft Fabric Semantic Model Row-Level Security (RLS) definitions only**.

The solution will:

1. Store individual RLS role definitions as TMDL files in GitHub.
2. Allow developers to add or modify RLS roles through feature branches and pull requests.
3. Automatically deploy proposed RLS changes to DEV when a pull request is created or updated.
4. Validate the deployment and show PASS/FAIL in the GitHub pull request.
5. Promote the same approved RLS definitions to TEST, UAT and PROD after environment-specific approvals.
6. Use Microsoft Fabric REST APIs for all semantic-model retrieval and updates.
7. Authenticate to Fabric using Microsoft Entra ID OAuth 2.0.
8. Use a Service Principal as the primary CI/CD authentication mechanism.
9. Optionally support interactive user authentication for local testing or administrative troubleshooting.
10. Preserve all non-RLS semantic-model definition components.

---

# 2. Environment Configuration

Every environment has its own Fabric workspace and semantic model.

Therefore the following values must be maintained as environment-specific configuration:

```text
workspaceId
semanticModelId
```

Recommended structure:

```text
projects/
└── sales/
    ├── project.json
    ├── roles/
    │   ├── abc.tmdl
    │   ├── FinanceRestricted.tmdl
    │   └── DynamicBusinessAccess.tmdl
    │
    └── environments/
        ├── dev.json
        ├── test.json
        ├── uat.json
        └── prod.json
```

Example `dev.json`:

```json
{
  "environment": "DEV",
  "workspaceId": "<DEV-WORKSPACE-ID>",
  "semanticModelId": "<DEV-SEMANTIC-MODEL-ID>"
}
```

Example `test.json`:

```json
{
  "environment": "TEST",
  "workspaceId": "<TEST-WORKSPACE-ID>",
  "semanticModelId": "<TEST-SEMANTIC-MODEL-ID>"
}
```

Equivalent configuration exists for UAT and PROD.

Therefore:

```text
                        Git
                         |
                 Same abc.tmdl
                         |
          +--------------+--------------+
          |              |              |
         DEV            TEST           UAT            PROD
          |              |              |              |
 Workspace A       Workspace B     Workspace C     Workspace D
 Semantic A        Semantic B      Semantic C      Semantic D
```

The **RLS TMDL does not change between environments**.

Only deployment target configuration changes.

This implements the principle:

> Build/approve once, promote the same RLS artifact across environments.

---

# 3. Common Project Configuration

Example `project.json`:

```json
{
  "projectKey": "sales",
  "roleSourcePath": "projects/sales/roles/",
  "roleDefinitionPathPrefix": "definition/roles/"
}
```

The role path prefix should be configurable rather than hard-coded.

Default:

```text
definition/roles/
```

Therefore:

```text
abc.tmdl
```

maps to:

```text
definition/roles/abc.tmdl
```

---

# 4. Authentication Architecture

The application supports two authentication modes.

```text
AuthenticationProvider
        |
        +-------------------------------+
        |                               |
Service Principal                 User Authentication
Primary CI/CD mode                Optional interactive mode
        |                               |
OAuth Client Credentials          OAuth Delegated Flow
        |                               |
MSAL ConfidentialClient           MSAL PublicClient
```

---

# 5. Authentication Mode 1 — Service Principal

## Recommended for GitHub Actions and automated deployments

Authentication protocol:

```text
OAuth 2.0 Client Credentials Grant
```

Python library:

```text
msal
```

The MSAL application type must be:

```python
msal.ConfidentialClientApplication
```

Microsoft documents `acquire_token_for_client()` as the MSAL Python method for acquiring an application token using client credentials.

---

## 5.1 Required Configuration

```text
tenantId
clientId
clientSecret
```

Authority:

```text
https://login.microsoftonline.com/<tenantId>
```

For example:

```python
AUTHORITY = f"https://login.microsoftonline.com/{tenant_id}"
```

MSAL supports tenant-specific authorities in this format.

Fabric scope:

```python
SCOPES = [
    "https://api.fabric.microsoft.com/.default"
]
```

Microsoft documents the Fabric resource scope for client-credential token acquisition as:

```text
https://api.fabric.microsoft.com/.default
```


---

# 6. Service Principal MSAL Implementation

Recommended implementation:

```python
import msal


class FabricServicePrincipalAuthenticator:

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str
    ):
        self.authority = (
            f"https://login.microsoftonline.com/{tenant_id}"
        )

        self.scopes = [
            "https://api.fabric.microsoft.com/.default"
        ]

        self.app = msal.ConfidentialClientApplication(
            client_id=client_id,
            authority=self.authority,
            client_credential=client_secret
        )

    def get_access_token(self) -> str:

        result = self.app.acquire_token_for_client(
            scopes=self.scopes
        )

        if "access_token" not in result:
            raise RuntimeError(
                "Fabric authentication failed: "
                + result.get(
                    "error_description",
                    result.get("error", "Unknown authentication error")
                )
            )

        return result["access_token"]
```

MSAL automatically uses its token cache when `acquire_token_for_client()` is called, avoiding an unnecessary token request when a suitable cached token exists.

---

# 7. Fabric API Authorization Header

Every Fabric REST call uses:

```http
Authorization: Bearer <access-token>
```

Example Python:

```python
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}
```

The Fabric API base URL is:

```text
https://api.fabric.microsoft.com
```

---

# 8. Important Service Principal Permission Model

There are two separate controls.

## Microsoft Entra authentication

This answers:

```text
Who is this application?
```

Handled through:

```text
Tenant ID
Client ID
Client credential
OAuth token
```

## Fabric authorization

This answers:

```text
What is this application allowed to modify?
```

The service principal must be authorized in Fabric.

Fabric also requires the tenant setting that allows service principals to use Fabric APIs to be enabled.

Therefore:

```text
Service Principal
       |
       +--> Microsoft Entra authentication
       |
       +--> Fabric tenant setting permits SP API access
       |
       +--> Fabric workspace/item permissions
       |
       v
Semantic Model API
```

---

# 9. Important Scope Clarification

For a **Service Principal**, use:

```python
["https://api.fabric.microsoft.com/.default"]
```

Do not treat:

```text
SemanticModel.ReadWrite.All
```

as the service principal runtime scope.

Microsoft explicitly states that Fabric REST delegated scopes apply to **user delegated access**. Direct service-principal and managed-identity authorization is governed by Fabric admin controls and artifact permissions.

Therefore:

```text
Service Principal
    ↓
https://api.fabric.microsoft.com/.default
```

while:

```text
Interactive User
    ↓
SemanticModel.ReadWrite.All
```

is the appropriate conceptual separation.

---

# 10. Required Fabric Permissions

The APIs used by this application require the following effective access.

### Get Semantic Model

Requires read permission.

The API supports:

```text
User
Service Principal
Managed Identity
```


### Get Semantic Model Definition

Requires:

```text
Read + Write
```

permission on the semantic model.

The API supports both users and service principals.

### Update Semantic Model Definition

Requires:

```text
Read + Write
```

permission on the semantic model.

The API also supports both users and service principals.

Therefore the deployment identity must ultimately have:

```text
READ + WRITE
```

access to the target semantic model.

---

# 11. Recommended Service Principal Configuration by Environment

For the POC, one Service Principal can be used:

```text
RLS-CICD-ServicePrincipal
```

with access to:

```text
DEV
TEST
UAT
PROD
```

However, production architecture should preferably isolate identities:

```text
rls-deployer-dev
rls-deployer-test
rls-deployer-uat
rls-deployer-prod
```

Then:

```text
DEV identity
    → DEV workspace only

TEST identity
    → TEST workspace only

UAT identity
    → UAT workspace only

PROD identity
    → PROD workspace only
```

This provides stronger blast-radius isolation.

---

# 12. Secret Management

Do not store the client secret in:

```text
project.json
environment JSON
source code
Git repository
```

For GitHub Actions use encrypted GitHub environment secrets.

Example:

```text
FABRIC_TENANT_ID
FABRIC_CLIENT_ID
FABRIC_CLIENT_SECRET
```

These can also be environment-specific:

```text
DEV:
FABRIC_CLIENT_ID
FABRIC_CLIENT_SECRET

TEST:
FABRIC_CLIENT_ID
FABRIC_CLIENT_SECRET

UAT:
FABRIC_CLIENT_ID
FABRIC_CLIENT_SECRET

PROD:
FABRIC_CLIENT_ID
FABRIC_CLIENT_SECRET
```

GitHub environment secrets are particularly useful because protected environment secrets are not exposed to the workflow until that environment's approval requirements have been satisfied.

For a production implementation, certificate credentials or workload federation can later replace client secrets without changing the Fabric client abstraction.

---

# 13. Optional Authentication Mode 2 — User Authentication

User authentication should be supported primarily for:

```text
Local development
Troubleshooting
Testing Fabric API access
Administrative/manual execution
```

It should NOT be the standard CI/CD authentication mechanism.

Use:

```python
msal.PublicClientApplication
```

Microsoft Fabric supports user identities for all three Semantic Model APIs used by this solution.

---

# 14. Interactive User Authentication

For desktop/local development, use:

```python
acquire_token_interactive()
```

Example:

```python
import msal


class FabricInteractiveAuthenticator:

    def __init__(
        self,
        tenant_id: str,
        client_id: str
    ):

        authority = (
            f"https://login.microsoftonline.com/{tenant_id}"
        )

        self.app = msal.PublicClientApplication(
            client_id=client_id,
            authority=authority
        )

        self.scopes = [
            "https://api.fabric.microsoft.com/"
            "SemanticModel.ReadWrite.All"
        ]

    def get_access_token(self) -> str:

        accounts = self.app.get_accounts()

        result = None

        if accounts:
            result = self.app.acquire_token_silent(
                scopes=self.scopes,
                account=accounts[0]
            )

        if not result:
            result = self.app.acquire_token_interactive(
                scopes=self.scopes
            )

        if "access_token" not in result:
            raise RuntimeError(
                result.get(
                    "error_description",
                    "Interactive authentication failed"
                )
            )

        return result["access_token"]
```

Microsoft recommends `acquire_token_interactive()` for interactive public-client scenarios; it opens the browser and supports PKCE. The app registration should include the desktop redirect URI:

```text
http://localhost
```


---

# 15. Delegated User Scope

For this application the most specific delegated permission is:

```text
SemanticModel.ReadWrite.All
```

because both Get Definition and Update Definition require it.

The fully qualified MSAL scope is:

```text
https://api.fabric.microsoft.com/SemanticModel.ReadWrite.All
```

A broader alternative is:

```text
https://api.fabric.microsoft.com/Item.ReadWrite.All
```

Fabric documents both as valid delegated permissions for these semantic-model APIs.

For least privilege, prefer:

```text
SemanticModel.ReadWrite.All
```

for interactive users.

---

# 16. Optional Device Code Authentication

For command-line environments where opening a browser locally is impractical, optionally support MSAL device-code flow:

```python
app = msal.PublicClientApplication(
    client_id,
    authority=authority
)

flow = app.initiate_device_flow(
    scopes=scopes
)

print(flow["message"])

result = app.acquire_token_by_device_flow(flow)
```

MSAL documents device-code flow for public clients/headless applications.

Thus user authentication modes can be:

```text
USER_INTERACTIVE
USER_DEVICE_CODE
```

while CI/CD uses:

```text
SERVICE_PRINCIPAL
```

---

# 17. Authentication Abstraction

Do not couple the Fabric API client directly to MSAL implementation details.

Recommended interface:

```python
from abc import ABC, abstractmethod


class TokenProvider(ABC):

    @abstractmethod
    def get_access_token(self) -> str:
        pass
```

Implementations:

```text
ServicePrincipalTokenProvider
InteractiveUserTokenProvider
DeviceCodeTokenProvider
```

Then:

```python
class FabricClient:

    def __init__(self, token_provider):
        self.token_provider = token_provider
```

This allows authentication methods to change without changing Fabric API logic.

---

# 18. Fabric API Sequence

The RLS deployment engine uses these Fabric APIs.

## Step 1 — Get Semantic Model

```http
GET https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/semanticModels/{semanticModelId}
```

Purpose:

```text
Verify configured workspaceId + semanticModelId combination
```

If this request succeeds:

```text
Target semantic model exists
Deployment identity can access it
```

If it fails:

```text
STOP deployment
```

---

# 19. Get Semantic Model Definition

```http
POST https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/semanticModels/{semanticModelId}/getDefinition?format=TMDL
```

This returns the complete semantic-model public definition.

Fabric explicitly supports TMDL and currently defaults to TMDL when no format is supplied. Explicitly specifying:

```text
format=TMDL
```

is still recommended for clarity.

Example:

```json
{
  "definition": {
    "parts": [
      {
        "path": "definition/database.tmdl",
        "payload": "...",
        "payloadType": "InlineBase64"
      },
      {
        "path": "definition/roles/abc.tmdl",
        "payload": "...",
        "payloadType": "InlineBase64"
      }
    ]
  }
}
```

---

# 20. Long-Running Operation Handling

`getDefinition` may return:

```text
200 OK
```

or:

```text
202 Accepted
```

For `202`, Fabric returns:

```text
Location
x-ms-operation-id
Retry-After
```


Generic process:

```text
API invocation
     |
     +--> 200
     |      |
     |      +--> use response
     |
     +--> 202
            |
            +--> capture operation ID
            |
            +--> wait Retry-After
            |
            +--> GET operation state
            |
            +--> Running
            |       |
            |       +--> repeat
            |
            +--> Succeeded
                    |
                    +--> get operation result
```

The same reusable LRO component should be used for:

```text
Get Definition
Update Definition
```

---

# 21. Core RLS Replace-or-Append Logic

Suppose Git contains:

```text
projects/sales/roles/abc.tmdl
```

Target Fabric path:

```text
definition/roles/abc.tmdl
```

Search:

```python
definition["parts"]
```

for:

```text
path == "definition/roles/abc.tmdl"
```

---

## Existing Role

If this path exists:

```text
definition/roles/abc.tmdl
```

then:

```text
REPLACE
```

only its `payload`.

Example:

```text
Existing:

definition/roles/abc.tmdl
payload = OLD_BASE64

                     ↓

Updated:

definition/roles/abc.tmdl
payload = NEW_BASE64
```

---

## New Role

If this path does not exist:

```text
APPEND
```

a new definition part:

```json
{
  "path": "definition/roles/abc.tmdl",
  "payload": "<base64 representation of abc.tmdl>",
  "payloadType": "InlineBase64"
}
```

Therefore:

```text
Does definition/roles/abc.tmdl exist?
             |
       +-----+-----+
       |           |
      YES          NO
       |           |
    REPLACE       APPEND
```

---

# 22. Preserve Complete Semantic Model

`updateDefinition` overrides the semantic-model definition supplied to Fabric. Microsoft describes the API explicitly as overriding the semantic model definition.

Therefore never send only:

```text
definition/roles/abc.tmdl
```

Instead:

```text
Get complete definition
       ↓
Modify RLS part
       ↓
Preserve everything else
       ↓
Send complete definition
```

Example:

```text
BEFORE

definition/database.tmdl
definition/model.tmdl
definition/tables/Customer.tmdl
definition/tables/Sales.tmdl
definition/roles/abc.tmdl
definition.pbism
.platform


AFTER

definition/database.tmdl           unchanged
definition/model.tmdl              unchanged
definition/tables/Customer.tmdl    unchanged
definition/tables/Sales.tmdl       unchanged
definition/roles/abc.tmdl          UPDATED
definition.pbism                   unchanged
.platform                          unchanged
```

---

# 23. Multiple RLS Changes

If one PR contains:

```text
abc.tmdl
finance.tmdl
executive.tmdl
```

perform:

```text
Get Definition once
       ↓
overlay abc
       ↓
overlay finance
       ↓
overlay executive
       ↓
Update Definition once
```

Do not call `updateDefinition` three times.

---

# 24. Update Semantic Model Definition

API:

```http
POST https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/semanticModels/{semanticModelId}/updateDefinition
```

Payload:

```json
{
  "definition": {
    "parts": [
      "...complete semantic model definition..."
    ]
  },
  "options": {
    "allowPurgeData": false
  }
}
```

For this RLS-only solution:

```text
allowPurgeData = false
```

should remain the default.

Fabric defines this option as permission to purge model data when definition changes require it, and its default is `false`.

RLS changes should not intentionally trigger destructive model-data purging.

---

# 25. Post-Deployment Verification

After `updateDefinition` reports success:

```text
Get Definition again
       ↓
find definition/roles/abc.tmdl
       ↓
decode payload
       ↓
compare against approved Git abc.tmdl
```

Successful deployment means:

```text
✓ Semantic model exists

✓ Authentication succeeded

✓ Get Definition succeeded

✓ Role resolved as APPEND or REPLACE

✓ Update Definition succeeded

✓ Fabric LRO succeeded if applicable

✓ Fresh Get Definition succeeded

✓ Target role exists

✓ Deployed role matches Git content
```

Only then should the GitHub deployment check pass.

---

# 26. GitHub Pull Request → DEV

Workflow:

```text
Developer
   |
   +--> feature branch
   |
   +--> changes abc.tmdl
   |
   +--> creates PR
            |
            v
     GitHub Actions
            |
            v
   Authenticate using MSAL
   Service Principal
            |
            v
       DEV config
            |
     workspaceId DEV
     semanticModelId DEV
            |
            v
      Fabric deployment
            |
            v
      Verification
            |
       +----+----+
       |         |
     PASS       FAIL
       |         |
       v         v
 GitHub PR ✓   GitHub PR ✗
```

Recommended trigger:

```yaml
on:
  pull_request:
    branches:
      - main
    types:
      - opened
      - synchronize
      - reopened
```

---

# 27. Higher-Environment Promotion

After DEV validation and PR approval:

```text
PR approved
    ↓
merge to MAIN
    ↓
same Git commit SHA
    ↓
TEST approval
    ↓
load test.json
    ↓
TEST workspaceId
TEST semanticModelId
    ↓
deploy
    ↓
validate
    ↓
UAT approval
    ↓
load uat.json
    ↓
deploy
    ↓
validate
    ↓
PROD approval
    ↓
load prod.json
    ↓
deploy
    ↓
validate
```

There is no rebuilding of the RLS definition between environments.

---

# 28. GitHub Environment Model

Configure:

```text
DEV
TEST
UAT
PROD
```

Recommended governance:

| Environment | Trigger | Approval |
|---|---|---|
| DEV | Pull request | Automatic |
| TEST | Approved PR merged | IT / Security |
| UAT | Successful TEST | Business / Visualization owner |
| PROD | Successful UAT | Production / Security owner |

Use GitHub Environment protection rules for TEST/UAT/PROD.

PROD should preferably have:

```text
Prevent self-review = enabled
```

---

# 29. Recommended Runtime Configuration Model

Global application configuration:

```json
{
  "fabricBaseUrl": "https://api.fabric.microsoft.com/v1",
  "authentication": {
    "mode": "SERVICE_PRINCIPAL",
    "scope": "https://api.fabric.microsoft.com/.default"
  }
}
```

Sensitive authentication values come from environment variables:

```text
FABRIC_TENANT_ID
FABRIC_CLIENT_ID
FABRIC_CLIENT_SECRET
```

Per-project configuration:

```json
{
  "projectKey": "sales",
  "roleDefinitionPathPrefix": "definition/roles/",
  "roleSourcePath": "projects/sales/roles/"
}
```

Per-environment configuration:

```json
{
  "environment": "PROD",
  "workspaceId": "...",
  "semanticModelId": "..."
}
```

---

# 30. Fabric Client Design

Recommended:

```python
class FabricClient:

    def __init__(
        self,
        token_provider,
        base_url="https://api.fabric.microsoft.com/v1"
    ):
        self.token_provider = token_provider
        self.base_url = base_url

    def get_semantic_model(
        self,
        workspace_id,
        semantic_model_id
    ):
        ...

    def get_semantic_model_definition(
        self,
        workspace_id,
        semantic_model_id,
        format="TMDL"
    ):
        ...

    def update_semantic_model_definition(
        self,
        workspace_id,
        semantic_model_id,
        definition
    ):
        ...

    def get_operation_state(
        self,
        operation_id
    ):
        ...

    def get_operation_result(
        self,
        operation_id
    ):
        ...

    def wait_for_operation(
        self,
        operation_id
    ):
        ...
```

---

# 31. Recommended Authentication Factory

```python
def create_token_provider(config):

    mode = config["authentication"]["mode"]

    if mode == "SERVICE_PRINCIPAL":
        return ServicePrincipalTokenProvider(...)

    if mode == "USER_INTERACTIVE":
        return InteractiveUserTokenProvider(...)

    if mode == "USER_DEVICE_CODE":
        return DeviceCodeTokenProvider(...)

    raise ValueError(
        f"Unsupported authentication mode: {mode}"
    )
```

This keeps the business/deployment logic completely independent of authentication type.

---

# 32. Error Handling

Authentication failures should be reported separately from Fabric authorization failures.

Example:

```text
AUTHENTICATION_FAILED
    Unable to obtain Entra access token

AUTHORIZATION_FAILED
    Access token valid but identity cannot access semantic model

SEMANTIC_MODEL_NOT_FOUND
    Configured workspace/model combination invalid

GET_DEFINITION_FAILED

UPDATE_DEFINITION_FAILED

LRO_FAILED

LRO_TIMEOUT

RLS_VERIFICATION_FAILED
```

Never output:

```text
Client secret
Access token
Refresh token
Complete Base64 semantic-model definition
```

into GitHub logs.

---

# 33. POC Authentication Acceptance Tests

### Service Principal

Given:

```text
tenantId
clientId
clientSecret
```

the application must successfully call:

```python
acquire_token_for_client(
    scopes=[
        "https://api.fabric.microsoft.com/.default"
    ]
)
```

and obtain an access token.

Then:

```text
GET Semantic Model → 200
```

must succeed.

---

### Invalid Service Principal

Invalid credentials:

```text
Token acquisition fails
        ↓
Fabric API must NOT be invoked
        ↓
GitHub job fails
```

---

### Valid Token but Missing Fabric Permission

```text
Token succeeds
        ↓
Fabric API returns authorization failure
        ↓
Pipeline reports FABRIC_AUTHORIZATION_FAILED
```

---

### Interactive User

User starts local application:

```text
Browser authentication
        ↓
Microsoft Entra login
        ↓
SemanticModel.ReadWrite.All
        ↓
Access token
        ↓
Fabric API
```

---

# 34. Final End-to-End POC Definition

The POC is complete when:

```text
1. Developer creates feature branch.

2. Developer adds or updates:
   projects/sales/roles/abc.tmdl

3. Developer creates PR.

4. GitHub Action starts.

5. Application loads DEV configuration.

6. Application reads:
   FABRIC_TENANT_ID
   FABRIC_CLIENT_ID
   FABRIC_CLIENT_SECRET

7. MSAL creates:
   ConfidentialClientApplication

8. Authority:
   https://login.microsoftonline.com/<tenantId>

9. Application calls:
   acquire_token_for_client()

10. Scope:
    https://api.fabric.microsoft.com/.default

11. Fabric access token returned.

12. Application calls:
    Get Semantic Model.

13. Application calls:
    Get Definition.

14. Any LRO is handled.

15. Application searches for:
    definition/roles/abc.tmdl

16. Existing:
    REPLACE.

    Missing:
    APPEND.

17. All unrelated semantic-model
    definition parts remain unchanged.

18. Application calls:
    Update Definition.

19. Any update LRO is handled.

20. Application calls Get Definition again.

21. Deployed role is compared
    against Git.

22. DEV GitHub check passes.

23. Required reviewer approves PR.

24. PR is merged.

25. TEST waits for GitHub
    Environment approval.

26. Application loads test.json.

27. Same Git RLS definition is
    deployed to configured TEST
    workspaceId + semanticModelId.

28. Same pattern applies to UAT.

29. Same pattern applies to PROD.

30. PROD uses the same approved Git
    commit/RLS definition.

31. All deployment operations and
    approvals are visible through GitHub.
```

## Core Architectural Principle

```text
Git
=
Source of Truth for governed RLS definitions

Fabric
=
Source of Truth for the complete live semantic model
```

Therefore every deployment follows:

```text
Git RLS TMDL
       +
Live Fabric complete definition
       |
       v
Replace existing role
OR
Append missing role
       |
       v
Complete updated Fabric definition
       |
       v
Update Semantic Model Definition
       |
       v
Re-read + verify
```

Authentication is deliberately separated from this deployment logic:

```text
GitHub CI/CD
       |
       v
MSAL
       |
       v
OAuth 2.0 Client Credentials
       |
       v
Service Principal
       |
       v
Fabric Access Token
       |
       v
Fabric Semantic Model APIs
```

Interactive user authentication remains an optional development and support mechanism, not the primary production deployment identity.