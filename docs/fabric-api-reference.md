# Microsoft Fabric REST API Reference

API Version: v1
Base URL: `https://api.fabric.microsoft.com/v1`
Last Validated: 2026-09-28

This document lists the five Fabric REST APIs used by this solution. No other Fabric API
(and no XMLA/TOM) is used for deployment.

| API | Solution Usage |
|---|---|
| Get Semantic Model | Validate target semantic model |
| Get Semantic Model Definition | Retrieve complete TMDL definition |
| Get Operation State | Poll asynchronous Fabric requests |
| Get Operation Result | Retrieve completed asynchronous result |
| Update Semantic Model Definition | Deploy complete modified definition |

## Get Semantic Model

```
GET /workspaces/{workspaceId}/semanticModels/{semanticModelId}
```

Validates that the configured `workspaceId` + `semanticModelId` identify an existing,
accessible semantic model. Requires read permission; supports users, service principals, and
managed identities.

## Get Semantic Model Definition

```
POST /workspaces/{workspaceId}/semanticModels/{semanticModelId}/getDefinition?format=TMDL
```

Retrieves the complete live semantic-model definition before applying any RLS modification.
`format=TMDL` is passed explicitly even though Fabric currently documents it as the default.
Requires read and write permission. Can return `200 OK` or `202 Accepted`. Fabric currently
blocks this API for a semantic model with an encrypted sensitivity label
(`ENCRYPTED_SENSITIVITY_LABEL_NOT_SUPPORTED`).

Example response:

```json
{
  "definition": {
    "parts": [
      { "path": "definition/database.tmdl", "payload": "<base64>", "payloadType": "InlineBase64" },
      { "path": "definition/roles/abc.tmdl", "payload": "<base64>", "payloadType": "InlineBase64" }
    ]
  }
}
```

## Get Operation State

```
GET /operations/{operationId}
```

Polls the state of an asynchronous Fabric request. Possible states: `NotStarted`, `Running`,
`Succeeded`, `Failed`.

## Get Operation Result

```
GET /operations/{operationId}/result
```

Retrieves the result of a completed long-running operation, most relevantly the resulting
semantic-model definition from an asynchronous Get Definition call. Follow the `Location`
header where provided rather than assuming every LRO exposes a separate result payload.

## Update Semantic Model Definition

```
POST /workspaces/{workspaceId}/semanticModels/{semanticModelId}/updateDefinition
```

Submits the complete semantic-model definition after applying RLS changes. **This API
overrides the definition supplied to it** — the request body must therefore always contain
every unrelated definition part unchanged, not just the modified RLS role(s). Supports both
`200 OK` and `202 Accepted`.

```json
{
  "definition": { "parts": ["...complete semantic model definition..."] },
  "options": { "allowPurgeData": false }
}
```

`allowPurgeData` must remain `false` (Fabric's own default) for this RLS solution.

## Long-running operations

Get Definition and Update Definition may return `202 Accepted` with `Location`,
`x-ms-operation-id`, and `Retry-After` headers. Poll `Get Operation State` and wait for
`Retry-After` seconds before polling, per Fabric's LRO guidance. This solution's shared poller
(`src/lro.py`) enforces a configurable timeout via `FABRIC_LRO_TIMEOUT_SECONDS` (default 900)
and treats `429 Too Many Requests` responses by respecting the returned `Retry-After` value.
