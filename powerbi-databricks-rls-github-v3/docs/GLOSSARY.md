# Glossary

| Term | Definition |
|---|---|
| **Power BI** | Microsoft's business intelligence platform for semantic models, reports, dashboards and analytics. |
| **Microsoft Fabric** | Microsoft's SaaS analytics platform that includes Power BI and other data/analytics workloads. |
| **Workspace** | A Fabric/Power BI collaborative container that holds semantic models, reports and other items and has Admin/Member/Contributor/Viewer roles. |
| **Semantic model** | The Power BI analytical model formerly commonly called a dataset. It contains tables, relationships, measures, partitions, security roles and metadata. |
| **RLS** | Row-Level Security. A semantic-model security mechanism that filters rows according to a role's DAX filter. |
| **OLS** | Object-Level Security. Security that hides/restricts model objects such as tables or columns. |
| **DAX** | Data Analysis Expressions. The expression language used for Power BI measures, calculated logic and RLS filters. |
| **`USERPRINCIPALNAME()`** | DAX function that returns the current user's UPN in the relevant Power BI security context; commonly used for dynamic RLS. |
| **UPN** | User Principal Name, normally formatted like `user@company.com`; commonly used as an Entra sign-in/user identifier. |
| **Microsoft Entra ID** | Microsoft's cloud identity and access management service, formerly Azure Active Directory. |
| **Security group** | An Entra group used to manage access for a set of users/principals. |
| **PBIX** | Traditional Power BI Desktop file containing report/model content in a packaged binary-oriented format. |
| **PBIP** | Power BI Project. A folder/project representation suitable for developer workflows and source control. |
| **TMDL** | Tabular Model Definition Language. Human-readable source representation of a Power BI/Analysis Services tabular semantic model. |
| **PBIR** | Power BI Enhanced Report Format. Source-control-friendly JSON/folder representation of report pages, visuals, bookmarks and metadata. |
| **`definition.pbir`** | PBIR metadata file that includes report settings and the semantic-model reference. |
| **`definition.pbism`** | Semantic-model definition-properties file used by the Fabric public-definition structure. |
| **Fabric connection** | Governed Fabric connection object representing how an item reaches/authenticates to a source such as Databricks. |
| **Connection binding** | Mapping a semantic-model data-source reference to a Fabric connection object. |
| **Databricks SQL Warehouse** | Databricks SQL compute endpoint frequently used by Power BI for SQL connectivity/DirectQuery. |
| **HTTP Path** | Databricks connection identifier for a SQL Warehouse endpoint, normally paired with the server hostname. |
| **Delta table** | Table stored in Delta Lake format with transaction-log based reliability and lakehouse capabilities. |
| **Unity Catalog** | Databricks governance/catalog layer for data and AI assets, permissions and metadata. |
| **DirectQuery** | Power BI mode where queries are sent to the source at interaction time instead of importing all model data. |
| **Import mode** | Power BI mode where data is loaded into the semantic model and refreshed periodically. |
| **SSO** | Single Sign-On. In a data-source context, can mean passing/using a user's identity to authenticate downstream. |
| **GitOps** | Operational approach where desired configuration/code is version-controlled and promoted through automated, reviewable workflows. |
| **GitHub Actions** | GitHub CI/CD automation engine used here to validate and deploy Fabric/Power BI assets. |
| **OIDC** | OpenID Connect. Used here for GitHub-to-Entra federated authentication without storing a long-lived Azure client secret. |
| **Service principal** | Application identity in Entra used for automation. |
| **Federated credential** | Entra trust configuration allowing an external OIDC identity, such as GitHub Actions, to obtain tokens for a service principal. |
| **Fabric REST API** | REST APIs for creating/updating/querying Fabric items, workspaces, connections and definitions. |
| **Power BI REST API** | REST APIs for Power BI operations such as refresh and DAX query execution. |
| **LRO** | Long-Running Operation. Fabric API pattern where a request returns an operation URL that is polled to completion. |
| **CODEOWNERS** | GitHub file that maps repository paths to required/expected reviewers. |
| **DEV / TEST / PROD** | Development, test/validation and production deployment environments. |
| **Entitlement** | Business authorization mapping that states what resources/data a user or group may access. |
| **Effective username** | Identity supplied to a model query for controlled impersonation/security testing. |
| **Role member** | User or group assigned to a tabular-model security role. |
| **Apache Arrow** | Columnar data-interchange format used by the newer Power BI DAX query API response. |
