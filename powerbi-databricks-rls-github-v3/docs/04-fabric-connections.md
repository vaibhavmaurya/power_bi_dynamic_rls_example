# Fabric Connections and Databricks

## What is a Fabric connection?

A Fabric connection is a governed connection object used by Fabric/Power BI to describe and
authenticate access to a data source. It separates credentials and connectivity from the
semantic-model source files.

For Databricks, the relevant information normally includes:

- Server/host name.
- SQL Warehouse HTTP path.
- Authentication method.
- Credential material or identity.
- Privacy level.
- Gateway/VNet configuration where applicable.

## Why binding is environment-specific

DEV, TEST and PROD may use different Databricks workspaces, warehouses, credentials or network
paths. The semantic model can stay logically identical while each environment binds the data
source reference to its own Fabric connection.

## V3 modes

`connection.mode = existing`
uses a pre-created governed connection and binds it.

`connection.mode = create`
calls Fabric's connection create API using a request JSON template. Secrets must be injected by
environment variables; never commit secrets.

Because Fabric exposes supported connection types and creation parameters dynamically, generate
or verify the exact Azure Databricks connection request against your tenant's
"List Supported Connection Types" result rather than inventing connector parameter names.

## SSO note

If the architecture uses DirectQuery + SSO, verify the Power BI/Databricks SSO constraints and
the exact connection configuration separately. RLS in the Power BI model and Databricks identity
passthrough are related but distinct controls.
