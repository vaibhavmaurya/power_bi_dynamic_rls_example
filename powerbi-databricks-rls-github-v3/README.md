# Proposed Approach – Dynamic Row-Level Security for Power BI using Databricks

Hi All,

Ahead of our discussion tomorrow, I wanted to summarize the proposed approach for implementing Row-Level Security (RLS) in Power BI, with Databricks as the data source.

What we are trying to achieve

When a user logs into Power BI, the report should automatically identify the user and display only the data that the user is authorized to access.

For example:

User A → India & Germany
User B → USA
User C → India

The objective is to avoid maintaining individual user-to-data access rules directly within Power BI.

How the solution will work

The proposed flow is:

User Login → Power BI RLS → Databricks User Entitlement → Authorized Data

1. Identify the logged-in user

Users authenticate to Power BI through Microsoft Entra ID. Within the Power BI semantic model, the DAX function USERPRINCIPALNAME() identifies the currently logged-in user, typically in the form user@company.com.

2. Maintain data entitlements in Databricks

A centrally governed entitlement table will be maintained in Databricks, for example:

User → Region / Market / Business Unit / other access dimension

Databricks therefore becomes the source of truth for determining which business data a particular user is authorized to access.

3. Apply Dynamic RLS in Power BI

The Power BI semantic model will contain a dynamic RLS rule that compares the logged-in user's identity with the entitlement data coming from Databricks.

Conceptually:

USERPRINCIPALNAME() → User Entitlement → Authorized Regions → Business Data

If John is entitled to India and Germany, the semantic model will return only India and Germany data. Unauthorized rows are filtered at the semantic-model level rather than simply hidden from a report visual.

4. Role membership in Power BI

After the PBIX is published, the relevant report consumers need to be associated with the RLS role in Power BI Service.

An Entra Security Group can optionally be used here to simplify administration for a large user population. However, the group does not determine which business data the user can see; that continues to come from the Databricks entitlement table.

Report and deployment approach

For the initial implementation, we can continue using the existing PBIX-based development and publishing process. PBIR or additional report-deployment automation is not required to implement RLS.

If required later, the semantic model and RLS definition can also be maintained as TMDL in GitHub and promoted through CI/CD for better version control, auditability and DEV → TEST → PROD consistency.

Responsibility of each layer
Microsoft Entra ID – authenticates the user.
Power BI – identifies the logged-in user and enforces Dynamic RLS.
Databricks – maintains the user-to-business-data entitlement.
Entra Security Group – optional – simplifies report access/RLS role membership administration.
GitHub/CI-CD – optional – provides version control and automated promotion of the semantic model/RLS configuration.

This keeps the solution relatively simple while providing centralized, scalable and auditable data-level authorization.

I will walk through the proposed architecture and implementation flow during tomorrow's discussion.

Thanks,
Vaibhav


Hi All,

Ahead of our discussion tomorrow, I wanted to summarize the proposed approach for implementing **Row-Level Security (RLS) in Power BI**, with Databricks as the data source.

## What we are trying to achieve

When a user logs into Power BI, the report should automatically identify the user and display **only the data that the user is authorized to access**.

For example:

- User A → India & Germany
- User B → USA
- User C → India

The objective is to avoid maintaining individual user-to-data access rules directly within Power BI.

## How the solution will work

The proposed flow is:

**User Login → Power BI RLS → Databricks User Entitlement → Authorized Data**

### 1. Identify the logged-in user

Users authenticate to Power BI through **Microsoft Entra ID**.

Within the Power BI semantic model, the DAX function:

`USERPRINCIPALNAME()`

identifies the currently logged-in user, typically in the form:

`user@company.com`

### 2. Maintain data entitlements in Databricks

A centrally governed entitlement table will be maintained in Databricks, for example:

`User → Region / Market / Business Unit / Other Access Dimension`

Example:

| User | Region |
|---|---|
| john@company.com | India |
| john@company.com | Germany |
| mary@company.com | USA |

Databricks therefore becomes the **source of truth for determining which business data a particular user is authorized to access**.

### 3. Apply Dynamic RLS in Power BI

The Power BI semantic model will contain a **Dynamic RLS rule** that compares the logged-in user's identity with the entitlement information coming from Databricks.

Conceptually:

`USERPRINCIPALNAME() → User Entitlement → Authorized Regions → Business Data`

For example, if John is entitled to **India and Germany**, the semantic model will return only India and Germany data.

The unauthorized rows are therefore **filtered at the semantic-model level**, rather than simply being hidden from a report visual.

### 4. RLS Role Membership in Power BI

Once the PBIX is published, the relevant report consumers need to be associated with the **RLS role in Power BI Service**.

An **Entra Security Group can optionally be used** here to simplify administration for a large number of users.

However, there is an important distinction:

**Entra Security Group → Who should be subject to/access the Power BI security role**

**Databricks Entitlement → What business data that individual user is authorized to see**

Therefore, the Entra group does **not determine the user's Region, Market or Business Unit access**. That entitlement continues to come from Databricks.

## End-to-End Flow

```text
Microsoft Entra ID
        |
        | Authentication
        v
Power BI Report
        |
        | USERPRINCIPALNAME()
        v
Dynamic Power BI RLS
        |
        v
Databricks User Entitlement
        |
        | User → Region / Market / BU
        v
Business Data
        |
        v
Authorized Rows Only
```




# Power BI + Databricks Dynamic RLS - V4

V4 intentionally focuses on the actual RLS requirement.

```text
Logged-in Power BI user
        |
USERPRINCIPALNAME()
        |
Power BI Dynamic RLS
        |
Databricks UserAccess entitlement
        |
Authorized rows
```

## V4 simplification

Removed from the core solution: Entra group as a data-entitlement step, group membership embedded in TMDL, PBIR deployment, Fabric Connection lifecycle, and report deployment.

The report can remain a normal **PBIX**. An Entra security group is optional for report/app access or for assigning many consumers to the RLS role in Power BI Service. **Databricks remains the source of user-to-data entitlement.**

TMDL/GitHub CI/CD remains only as optional industrialization for the semantic model and RLS definition.
