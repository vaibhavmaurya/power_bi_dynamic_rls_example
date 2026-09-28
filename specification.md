# Centralized Power BI RLS Governance Using Microsoft Fabric REST APIs

## 1. Purpose

This solution provides centralized governance, version control, validation, deployment, and promotion of **Power BI / Microsoft Fabric Semantic Model Row-Level Security (RLS) definitions**.

The scope is intentionally restricted to RLS. Report development, visual development, measures, tables, relationships, Power Query, semantic-model design, and other report-development activities remain outside this solution.

The solution uses:

```text
GitHub
GitHub Actions
Microsoft Fabric REST APIs
Microsoft Entra ID OAuth 2.0
MSAL Python
TMDL RLS definitions
```

The primary deployment identity is a **Microsoft Entra Service Principal**.

Interactive user authentication is supported as an optional mechanism for local testing and troubleshooting.

---

# 2. Core Architectural Principles

The architecture follows these principles.

| Principle | Design |
|---|---|
| RLS source of truth | GitHub |
| Full semantic model source of truth | Microsoft Fabric |
| Deployment mechanism | Microsoft Fabric REST APIs |
| Authentication | Microsoft Entra OAuth 2.0 |
| CI/CD authentication | Service Principal using MSAL |
| DEV deployment | Automatically on Pull Request |
| Higher environments | GitHub Environment approval gates |
| RLS update | Replace existing role or append new role |
| Semantic-model protection | Retrieve complete live definition before updating |
| Promotion model | Same approved Git commit promoted unchanged |
| Environment differences | Workspace ID and Semantic Model ID only |
| RLS deletion | Out of scope for initial POC |

A critical Fabric behavior drives the design:

> `updateDefinition` overrides the semantic-model definition supplied to it.

Therefore the application must **never send only the changed RLS file**.

Instead:

```text
Get complete Fabric semantic model definition
                    ↓
Overlay changed RLS definition(s)
                    ↓
Preserve every other definition part
                    ↓
Send complete updated definition
                    ↓
Re-read definition
                    ↓
Verify deployed RLS
```

Microsoft documents `Update Semantic Model Definition` as overriding the definition for the specified semantic model.

---

# 3. High-Level Architecture

```text
                    ┌─────────────────────────┐
                    │ Visualization / RLS Team│
                    └────────────┬────────────┘
                                 │
                         Create Feature Branch
                                 │
                         Add / Update RLS TMDL
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │      GitHub Repo        │
                    └────────────┬────────────┘
                                 │
                           Pull Request
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     GitHub Actions      │
                    │   PR → DEV Workflow     │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ MSAL Authentication     │
                    │ Service Principal       │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Fabric REST APIs        │
                    │                         │
                    │ Get Semantic Model      │
                    │ Get Definition          │
                    │ LRO APIs                │
                    │ Update Definition       │
                    └────────────┬────────────┘
                                 │
                          DEV Validation
                                 │
                                 ▼
                       GitHub PR PASS / FAIL
                                 │
                         Review + PR Merge
                                 │
                                 ▼
                  TEST → UAT → PROD Promotion
                    with approval at each gate
```

---

# 4. Repository Structure

Recommended POC structure:

```text
powerbi-rls-governance/
│
├── projects/
│   ├── sales/
│   │   ├── project.json
│   │   │
│   │   ├── roles/
│   │   │   ├── abc.tmdl
│   │   │   ├── FinanceRestricted.tmdl
│   │   │   └── DynamicBusinessAccess.tmdl
│   │   │
│   │   └── environments/
│   │       ├── dev.json
│   │       ├── test.json
│   │       ├── uat.json
│   │       └── prod.json
│   │
│   └── another-project/
│
├── src/
│   ├── authentication.py
│   ├── fabric_client.py
│   ├── lro.py
│   ├── change_detection.py
│   ├── role_overlay.py
│   ├── deploy.py
│   └── verify.py
│
├── tests/
│   ├── test_authentication.py
│   ├── test_lro.py
│   ├── test_role_overlay.py
│   ├── test_change_detection.py
│   └── test_deployment.py
│
├── docs/
│   ├── architecture.md
│   ├── fabric-api-reference.md
│   ├── authentication.md
│   └── github-cicd.md
│
└── .github/
    ├── CODEOWNERS
    └── workflows/
        ├── pr-dev.yml
        └── promote.yml
```

---

# 5. Project Configuration

Example:

```json
{
  "projectKey": "sales",
  "roleSourcePath": "projects/sales/roles/",
  "roleDefinitionPathPrefix": "definition/roles/"
}
```

The TMDL role path prefix must be configurable.

The default is:

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

The implementation must ultimately compare against the exact `path` returned by Fabric's `getDefinition`.

---

# 6. Environment Configuration

Each environment maintains its own:

```text
workspaceId
semanticModelId
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

The same approach applies to UAT and PROD.

Conceptually:

```text
                    Same Approved Git RLS

                           abc.tmdl
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
            DEV               TEST              UAT              PROD
             │                 │                 │                 │
      Workspace DEV      Workspace TEST     Workspace UAT     Workspace PROD
      Semantic DEV       Semantic TEST      Semantic UAT      Semantic PROD
```

The role definition itself must not be rebuilt or changed between environments.

---

# 7. Authentication Design

## 7.1 Primary Authentication

The primary CI/CD authentication mechanism is:

```text
OAuth 2.0 Client Credentials
        +
Microsoft Entra Service Principal
        +
MSAL Python
```

Python library:

```text
msal
```

MSAL class:

```python
msal.ConfidentialClientApplication
```

Authority:

```text
https://login.microsoftonline.com/<tenantId>
```

Scope:

```text
https://api.fabric.microsoft.com/.default
```

Token method:

```python
acquire_token_for_client()
```

MSAL documents `acquire_token_for_client()` as the method for obtaining an access token as the application itself using client credentials.

---

# 8. Service Principal Authentication Implementation

Recommended implementation:

```python
import msal


class ServicePrincipalTokenProvider:

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
                "Authentication failed: "
                + result.get(
                    "error_description",
                    result.get("error", "Unknown error")
                )
            )

        return result["access_token"]
```

MSAL also uses its token cache when `acquire_token_for_client()` is invoked and requests another token only when necessary.

---

# 9. Authentication Configuration

Authentication secrets must not be stored in project or environment JSON files.

Use environment variables or GitHub secrets:

```text
FABRIC_TENANT_ID
FABRIC_CLIENT_ID
FABRIC_CLIENT_SECRET
```

The separation is:

```text
Environment deployment configuration
------------------------------------
workspaceId
semanticModelId


Authentication configuration
----------------------------
tenantId
clientId
clientSecret
```

These concerns must remain independent.

---

# 10. Optional User Authentication

Interactive user authentication is optional and intended for:

```text
Local development
API troubleshooting
Administrative testing
Developer validation
```

It must not be the default GitHub CI/CD authentication method.

Use:

```python
msal.PublicClientApplication
```

Recommended delegated scope:

```text
https://api.fabric.microsoft.com/SemanticModel.ReadWrite.All
```

Fabric documents `SemanticModel.ReadWrite.All` or `Item.ReadWrite.All` as valid delegated scopes for Get Definition and Update Definition.

Example:

```python
import msal


class InteractiveUserTokenProvider:

    def __init__(self, tenant_id, client_id):

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

    def get_access_token(self):

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
                    "Authentication failed"
                )
            )

        return result["access_token"]
```

---

# 11. Authentication Abstraction

Fabric API code must not directly depend on a particular MSAL authentication mechanism.

Recommended abstraction:

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
DeviceCodeTokenProvider        optional
```

Then:

```python
class FabricClient:

    def __init__(self, token_provider):
        self.token_provider = token_provider
```

This makes authentication replaceable without changing Fabric deployment logic.

---

# 12. Fabric REST API Reference

Base URL:

```text
https://api.fabric.microsoft.com/v1
```

The POC uses the following Fabric APIs.

| Purpose | Method | API |
|---|---|---|
| Verify semantic model | GET | `/workspaces/{workspaceId}/semanticModels/{semanticModelId}` |
| Retrieve semantic definition | POST | `/workspaces/{workspaceId}/semanticModels/{semanticModelId}/getDefinition?format=TMDL` |
| Poll long-running operation | GET | `/operations/{operationId}` |
| Retrieve LRO result | GET | `/operations/{operationId}/result` |
| Update semantic definition | POST | `/workspaces/{workspaceId}/semanticModels/{semanticModelId}/updateDefinition` |

These APIs are the approved Fabric API surface for the initial POC.

The implementation must not silently switch to XMLA/TOM.

---

# 13. API 1 — Get Semantic Model

Purpose:

```text
Validate that the configured:

workspaceId
+
semanticModelId

identify an existing and accessible semantic model.
```

Request:

```http
GET https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/semanticModels/{semanticModelId}
```

Fabric documents this API as returning the properties of a semantic model and requiring read permission. It supports users, service principals, and managed identities.

Official reference:

```text
Microsoft Learn
Fabric REST API
Semantic Model
Get Semantic Model
API Version: v1
```

---

# 14. API 2 — Get Semantic Model Definition

Purpose:

```text
Retrieve the complete live semantic-model definition
before applying an RLS modification.
```

Request:

```http
POST https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/semanticModels/{semanticModelId}/getDefinition?format=TMDL
```

`TMDL` should be explicitly specified even though Fabric currently documents it as the default definition format.

Example response:

```json
{
  "definition": {
    "parts": [
      {
        "path": "definition/database.tmdl",
        "payload": "<base64>",
        "payloadType": "InlineBase64"
      },
      {
        "path": "definition/roles/abc.tmdl",
        "payload": "<base64>",
        "payloadType": "InlineBase64"
      }
    ]
  }
}
```

Fabric documents that Get Definition requires read and write permission and can return either `200 OK` or `202 Accepted`.

An important limitation is that Fabric currently blocks this API for a semantic model with an encrypted sensitivity label.

Official reference:

```text
Microsoft Learn
Fabric REST API
Semantic Model
Get Semantic Model Definition
API Version: v1
```

---

# 15. API 3 — Long Running Operation State

Get Definition and Update Definition may return:

```text
202 Accepted
```

When that happens, Fabric returns:

```text
Location
x-ms-operation-id
Retry-After
```

Fabric's LRO documentation defines these headers and recommends waiting for the provided `Retry-After` duration before polling.

Request:

```http
GET https://api.fabric.microsoft.com/v1/operations/{operationId}
```

Possible states include:

```text
NotStarted
Running
Succeeded
Failed
```

Fabric documents this API as returning the current state of the long-running operation.

Official reference:

```text
Microsoft Learn
Fabric REST API
Core
Long Running Operations
Get Operation State
API Version: v1
```

---

# 16. API 4 — Long Running Operation Result

When an asynchronous operation produces a result, retrieve it using:

```http
GET https://api.fabric.microsoft.com/v1/operations/{operationId}/result
```

This is particularly relevant to asynchronous `getDefinition`, because the application needs the resulting semantic-model definition.

Fabric documents this API as returning the result of a completed long-running operation.

Official reference:

```text
Microsoft Learn
Fabric REST API
Core
Long Running Operations
Get Operation Result
API Version: v1
```

The implementation should follow the `Location` returned by Fabric where appropriate rather than making assumptions about whether every LRO has a separate result payload. Fabric's LRO documentation states that the `Location` header changes to the result location once an operation completes when a result exists.

---

# 17. API 5 — Update Semantic Model Definition

Purpose:

```text
Submit the complete semantic-model definition
after applying RLS changes.
```

Request:

```http
POST https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/semanticModels/{semanticModelId}/updateDefinition
```

Example payload:

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

Fabric explicitly states that this API **overrides the definition** for the specified semantic model. It supports both immediate `200 OK` and asynchronous `202 Accepted` responses.

For this RLS solution:

```text
allowPurgeData = false
```

must remain the default.

Fabric also documents `false` as the default value for this option.

Official reference:

```text
Microsoft Learn
Fabric REST API
Semantic Model
Update Semantic Model Definition
API Version: v1
```

---

# 18. Common Fabric Request Headers

Every Fabric request uses:

```http
Authorization: Bearer <access-token>
Content-Type: application/json
```

Example:

```python
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
```

Tokens must never be written to GitHub logs.

---

# 19. Long-Running Operation Handler

The application should implement one common LRO processor.

Pseudo-flow:

```text
Call Fabric API
      │
      ├── 200 OK
      │      │
      │      └── return response
      │
      └── 202 Accepted
             │
             ├── capture Location
             ├── capture operation ID
             └── capture Retry-After
                      │
                      ▼
                Wait Retry-After
                      │
                      ▼
                Get Operation State
                      │
             ┌────────┼────────┐
             │        │        │
          Running   Failed   Succeeded
             │        │        │
           repeat    fail      ▼
                            retrieve result
                            when applicable
```

Recommended configurable timeout:

```text
FABRIC_LRO_TIMEOUT_SECONDS=900
```

The implementation must respect Fabric's `Retry-After` header for polling and throttling responses.

---

# 20. RLS Replace-or-Append Requirement

Suppose Git contains:

```text
projects/sales/roles/abc.tmdl
```

The target semantic model definition path is:

```text
definition/roles/abc.tmdl
```

The application retrieves:

```python
definition["parts"]
```

and searches for an exact path match:

```python
part["path"] == "definition/roles/abc.tmdl"
```

The behavior is:

```text
Does definition/roles/abc.tmdl exist?
                  │
           ┌──────┴──────┐
           │             │
          YES            NO
           │             │
        REPLACE         APPEND
```

---

# 21. Existing Role — Replace

If Fabric already contains:

```text
definition/roles/abc.tmdl
```

the application must replace the existing payload with the Base64 representation of the Git `abc.tmdl`.

Example:

```text
BEFORE

path:
definition/roles/abc.tmdl

payload:
OLD_BASE64


AFTER

path:
definition/roles/abc.tmdl

payload:
NEW_BASE64
```

The existing item is replaced by `path`.

No unrelated semantic-model definition element should be modified.

---

# 22. New Role — Append

If:

```text
definition/roles/abc.tmdl
```

does not exist, append:

```json
{
  "path": "definition/roles/abc.tmdl",
  "payload": "<BASE64-ENCODED-ABC-TMDL>",
  "payloadType": "InlineBase64"
}
```

to:

```text
definition.parts[]
```

---

# 23. Role Overlay Function

Recommended implementation contract:

```python
def overlay_role(
    definition: dict,
    role_file_name: str,
    role_content: str,
    role_path_prefix: str = "definition/roles/"
) -> dict:
    ...
```

Conceptual implementation:

```python
import base64


target_path = (
    role_path_prefix
    + role_file_name
)

payload = base64.b64encode(
    role_content.encode("utf-8")
).decode("ascii")


matches = [
    part
    for part in definition["parts"]
    if part["path"] == target_path
]


new_part = {
    "path": target_path,
    "payload": payload,
    "payloadType": "InlineBase64"
}


if len(matches) > 1:
    raise DuplicateDefinitionPartError(
        target_path
    )

elif len(matches) == 1:

    replace existing part

    operation = "REPLACE"

else:

    definition["parts"].append(
        new_part
    )

    operation = "APPEND"
```

The operation result should expose:

```text
targetPath
operation = APPEND | REPLACE
```

for GitHub reporting.

---

# 24. Multiple RLS Changes

If one PR changes:

```text
abc.tmdl
finance.tmdl
executive.tmdl
```

perform:

```text
Get Definition
      ↓
Overlay abc
      ↓
Overlay finance
      ↓
Overlay executive
      ↓
Update Definition ONCE
```

Do not invoke Update Definition separately for every role.

This reduces race conditions and avoids intermediate model states.

---

# 25. Preservation Rule

Suppose Fabric returns:

```text
definition/database.tmdl
definition/model.tmdl
definition/tables/Customer.tmdl
definition/tables/Sales.tmdl
definition/relationships.tmdl
definition/roles/abc.tmdl
definition.pbism
.platform
```

and `abc.tmdl` changes.

The outgoing payload must remain:

```text
definition/database.tmdl              unchanged
definition/model.tmdl                 unchanged
definition/tables/Customer.tmdl       unchanged
definition/tables/Sales.tmdl          unchanged
definition/relationships.tmdl         unchanged
definition/roles/abc.tmdl             changed
definition.pbism                      unchanged
.platform                             unchanged
```

This rule exists because Fabric Update Definition overrides the definition supplied to the API.

---

# 26. Concurrent Change Protection

A read-modify-write API can overwrite changes made between retrieval and update.

The POC should therefore implement:

```text
Get definition D0
       ↓
Prepare proposed RLS overlay
       ↓
Get latest definition D1
       ↓
Compare non-target definition parts
       ↓
Changed?
   │
   ├── YES → ABORT
   │
   └── NO
        ↓
Apply RLS overlay to latest definition
        ↓
Update Definition
```

GitHub Actions concurrency should also prevent parallel deployments to the same:

```text
project + environment
```

Example groups:

```text
sales-dev
sales-test
sales-uat
sales-prod
```

---

# 27. Pull Request to DEV Workflow

A developer:

```text
Creates branch
      ↓
Adds/updates abc.tmdl
      ↓
Pushes branch
      ↓
Creates Pull Request
```

Recommended GitHub trigger:

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

Deployment sequence:

```text
Pull Request
      ↓
Detect changed role files
      ↓
Load project configuration
      ↓
Load DEV configuration
      ↓
Authenticate through MSAL
      ↓
Get Semantic Model
      ↓
Get Definition
      ↓
Handle LRO if required
      ↓
Overlay changed roles
      ↓
Update Definition
      ↓
Handle LRO if required
      ↓
Get Definition again
      ↓
Verify deployed content
      ↓
Publish GitHub check
```

---

# 28. DEV Pull Request Result

GitHub should expose a check named:

```text
RLS / DEV Deployment
```

Example success:

```text
RLS DEV Deployment

Project:
Sales

Environment:
DEV

Commit:
57f88...

Roles:

abc.tmdl
REPLACED ✓

FinanceRestricted.tmdl
APPENDED ✓


Fabric Validation:

Authentication              ✓
Semantic Model              ✓
Get Definition              ✓
RLS Overlay                 ✓
Update Definition           ✓
Post-deployment verification ✓

RESULT: SUCCESS
```

A failed deployment must make the PR check fail.

The PR should not be mergeable while the required deployment check is failing.

---

# 29. PR Review

Use GitHub:

```text
CODEOWNERS
```

for:

```text
/projects/**/roles/
```

Example:

```text
/projects/**/roles/ @rls-security-team
```

The protected main branch should require:

```text
Successful RLS / DEV Deployment
+
Required reviewer approval
```

before merge.

---

# 30. Promotion to Higher Environments

DEV is different from TEST/UAT/PROD.

DEV validates the proposed pull request.

TEST, UAT and PROD receive only **reviewed and merged code**.

```text
Feature Branch
      ↓
Pull Request
      ↓
DEV Deployment
      ↓
Validation
      ↓
Approval
      ↓
Merge to Main
      ↓
Exact Git Commit
      ↓
TEST Approval
      ↓
TEST Deployment
      ↓
TEST Validation
      ↓
UAT Approval
      ↓
UAT Deployment
      ↓
UAT Validation
      ↓
PROD Approval
      ↓
PROD Deployment
      ↓
PROD Validation
```

---

# 31. GitHub Environment Model

Recommended environments:

| Environment | Deployment | Approval |
|---|---|---|
| DEV | Automatic from PR | No deployment approval |
| TEST | From merged commit | IT / Security |
| UAT | After successful TEST | Business / Visualization Owner |
| PROD | After successful UAT | Production / Security Owner |

The same Git commit SHA must be promoted to all higher environments.

The deployment process simply loads:

```text
test.json
uat.json
prod.json
```

to determine the correct:

```text
workspaceId
semanticModelId
```

---

# 32. Deployment Identity by Environment

For the POC, a single service principal can be used.

Production can later move to:

```text
rls-deployer-dev
rls-deployer-test
rls-deployer-uat
rls-deployer-prod
```

This provides workspace-level blast-radius isolation.

No change to deployment code is required because authentication is abstracted behind `TokenProvider`.

---

# 33. Post-Deployment Validation

After Update Definition succeeds:

```text
Get Definition again
      ↓
Locate expected RLS path
      ↓
Decode Base64 payload
      ↓
Normalize line endings
      ↓
Compare against Git TMDL
```

A successful deployment requires:

```text
Semantic model exists                  PASS
Authentication                         PASS
Definition retrieved                   PASS
Target path determined                 PASS
Role appended/replaced                 PASS
Definition updated                     PASS
LRO completed                          PASS
Definition re-read                     PASS
RLS path exists                        PASS
RLS payload matches Git                PASS
```

Only then should the deployment be marked successful.

---

# 34. RLS Deletion

Role deletion is deliberately excluded from the first POC.

Behavior:

```text
ADD       supported
UPDATE    supported
DELETE    rejected
RENAME    rejected
```

Removing a role can weaken security, so a future deletion mechanism should require an explicit delete operation and stronger approval.

Deleting `abc.tmdl` from Git must therefore **not automatically delete** the Fabric role.

---

# 35. Fabric Client Interface

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
        pass

    def get_semantic_model_definition(
        self,
        workspace_id,
        semantic_model_id,
        definition_format="TMDL"
    ):
        pass

    def update_semantic_model_definition(
        self,
        workspace_id,
        semantic_model_id,
        definition
    ):
        pass

    def get_operation_state(
        self,
        operation_id
    ):
        pass

    def get_operation_result(
        self,
        operation_id
    ):
        pass

    def wait_for_operation(
        self,
        operation_id,
        retry_after=None
    ):
        pass
```

---

# 36. Error Model

The application should expose meaningful errors such as:

```text
AUTHENTICATION_FAILED

FABRIC_AUTHORIZATION_FAILED

SEMANTIC_MODEL_NOT_FOUND

GET_DEFINITION_FAILED

ENCRYPTED_SENSITIVITY_LABEL_NOT_SUPPORTED

DUPLICATE_ROLE_PATH

ROLE_PATH_COLLISION

CONCURRENT_MODEL_CHANGE_DETECTED

UPDATE_DEFINITION_FAILED

LRO_FAILED

LRO_TIMEOUT

FABRIC_RATE_LIMITED

POST_DEPLOYMENT_VALIDATION_FAILED

ROLE_DELETE_NOT_SUPPORTED
```

Fabric documents `429 Too Many Requests` and returns `Retry-After`; the client must respect that value.

---

# 37. Security Requirements

The application must never log:

```text
Client secrets
Access tokens
Refresh tokens
GitHub secrets
Complete Base64 semantic-model payloads
```

For the POC, client-secret authentication using MSAL is acceptable.

A production evolution can replace the client secret with:

```text
Certificate authentication
or
Workload identity federation
```

without changing the Fabric deployment architecture.

---

# 38. Unit Test Requirements

Mandatory unit-test coverage should include:

```text
Service principal authentication success
Service principal authentication failure

Existing role → REPLACE

Missing role → APPEND

Multiple roles → single updated definition

Non-RLS definition parts preserved

Base64 encoding/decoding

Duplicate role path rejected

Role deletion rejected

Get Definition 200 path

Get Definition 202 LRO path

Update Definition 200 path

Update Definition 202 LRO path

Running → Succeeded LRO

Failed LRO

LRO timeout

429 Retry-After

Concurrent non-RLS change detected

Post-deployment RLS verification
```

The most important invariant is:

```text
For every definition part that is NOT
a requested RLS target path:

BEFORE.path    == AFTER.path
BEFORE.payload == AFTER.payload
```

---

# 39. POC Acceptance Scenario — Existing Role

Initial Fabric model:

```text
definition/database.tmdl
definition/model.tmdl
definition/tables/customer.tmdl
definition/roles/abc.tmdl
definition.pbism
.platform
```

Git PR changes:

```text
abc.tmdl
```

Application finds:

```text
definition/roles/abc.tmdl
```

Result:

```text
REPLACE
```

Expected GitHub result:

```text
RLS / DEV Deployment ✓

abc.tmdl
Operation: REPLACED
Verification: PASSED
```

---

# 40. POC Acceptance Scenario — New Role

Fabric does not contain:

```text
definition/roles/NewFinanceRole.tmdl
```

Git introduces:

```text
NewFinanceRole.tmdl
```

Result:

```text
APPEND
```

Expected GitHub result:

```text
RLS / DEV Deployment ✓

NewFinanceRole.tmdl
Operation: APPENDED
Verification: PASSED
```

---

# 41. Complete POC End-to-End Flow

```text
Developer creates feature branch
             ↓
Developer changes abc.tmdl
             ↓
Developer creates PR
             ↓
GitHub Actions starts
             ↓
Load DEV workspaceId + semanticModelId
             ↓
Create MSAL ConfidentialClientApplication
             ↓
Authority:
https://login.microsoftonline.com/<tenantId>
             ↓
Scope:
https://api.fabric.microsoft.com/.default
             ↓
acquire_token_for_client()
             ↓
Fabric Access Token
             ↓
GET Semantic Model
             ↓
Semantic model exists
             ↓
POST Get Definition?format=TMDL
             ↓
200?
 │
 ├── YES → definition available
 │
 └── NO / 202
          ↓
     Poll LRO
          ↓
     Get Operation Result
             ↓
Search:
definition/roles/abc.tmdl
             ↓
       ┌─────┴─────┐
       │           │
     Exists      Missing
       │           │
    REPLACE       APPEND
       └─────┬─────┘
             ↓
Preserve all other definition parts
             ↓
POST Update Definition
             ↓
200?
 │
 ├── YES
 │
 └── 202
       ↓
   Poll LRO
             ↓
Update succeeds
             ↓
Get Definition again
             ↓
Verify abc.tmdl against Git
             ↓
GitHub DEV Check = SUCCESS
             ↓
Reviewer approves PR
             ↓
Merge to main
             ↓
TEST approval
             ↓
Load TEST workspaceId + semanticModelId
             ↓
Deploy same Git commit
             ↓
Verify
             ↓
UAT approval
             ↓
Deploy same Git commit
             ↓
Verify
             ↓
PROD approval
             ↓
Deploy same Git commit
             ↓
Verify
```

---

# 42. API Reference Documentation

The repository must maintain:

```text
docs/fabric-api-reference.md
```

Header:

```text
Microsoft Fabric REST API Reference
API Version: v1
Base URL: https://api.fabric.microsoft.com/v1
Last Validated: 2026-09-28
```

The reference must contain the five APIs used by this solution.

| API | Solution Usage |
|---|---|
| Get Semantic Model | Validate target semantic model |
| Get Semantic Model Definition | Retrieve complete TMDL definition |
| Get Operation State | Poll asynchronous Fabric requests |
| Get Operation Result | Retrieve completed asynchronous result |
| Update Semantic Model Definition | Deploy complete modified definition |

Official Microsoft documentation references maintained for this solution are: **Get Semantic Model**, **Get Semantic Model Definition**, **Update Semantic Model Definition**, **Get Operation State**, **Get Operation Result**, and the general Fabric **Long Running Operations** guidance.

---

# 43. Authentication Reference Documentation

The repository must also maintain:

```text
docs/authentication.md
```

Primary implementation:

```text
Authentication:
OAuth 2.0 Client Credentials

Identity:
Microsoft Entra Service Principal

Python Library:
msal

MSAL Application:
ConfidentialClientApplication

Authority:
https://login.microsoftonline.com/<tenantId>

Scope:
https://api.fabric.microsoft.com/.default

Token Method:
acquire_token_for_client()
```

Optional local authentication:

```text
Authentication:
OAuth delegated user authentication

MSAL Application:
PublicClientApplication

Scope:
https://api.fabric.microsoft.com/SemanticModel.ReadWrite.All
```

---

# 44. Explicit POC Non-Goals

The POC does not:

```text
Modify Power BI reports

Modify visual definitions

Modify measures

Modify tables

Modify relationships

Modify Power Query

Manage semantic-model development

Use XMLA/TOM for deployment

Automatically delete RLS roles

Automatically rename roles

Allow failed deployments to promote

Generate different RLS TMDL per environment
```

---

# 45. Definition of Done

The POC is considered complete when a developer can change or add an RLS TMDL file through a GitHub pull request and the system successfully:

```text
Authenticates using MSAL and a Service Principal

Validates the configured Fabric semantic model

Retrieves its complete TMDL definition

Processes Fabric long-running operations

Detects whether the role path already exists

Replaces an existing RLS role

or

Appends a new RLS role

Preserves all unrelated definition parts

Updates the semantic model using Fabric REST API

Re-reads the semantic model

Verifies deployed RLS content against Git

Displays deployment status in the Pull Request

Requires review before merge

Promotes the identical approved Git commit through
TEST → UAT → PROD

Uses environment-specific workspaceId and semanticModelId

Records success/failure for every promotion
```

The architectural contract is therefore:

```text
GitHub
=
Source of Truth for governed RLS definitions


Microsoft Fabric
=
Source of Truth for complete live semantic-model definition


Environment configuration
=
workspaceId + semanticModelId


Authentication
=
Microsoft Entra OAuth 2.0
using MSAL


Deployment
=
Get complete definition
→ Replace/Append RLS
→ Update complete definition
→ Re-read
→ Verify
```